from __future__ import absolute_import, unicode_literals

from json import loads

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.views import main as main_views
from django.forms.widgets import Select
from django.shortcuts import render
from django.utils.html import escape, format_html, mark_safe
from django.utils.translation import gettext_lazy as _

from celery import current_app
from celery import states
from celery.task.control import broadcast, revoke, rate_limit
from celery.utils import cached_property
from celery.utils.text import abbrtask

from .admin_utils import action, display_field, fixedwidth
from .models import (
    TaskState, WorkerState,
    PeriodicTask, IntervalSchedule, CrontabSchedule,
    PeriodicTasks
)
from .humanize import naturaldate
from .utils import is_database_scheduler, make_aware

from django.utils.encoding import force_str


TASK_STATE_COLORS = {states.SUCCESS: 'green',
                     states.FAILURE: 'red',
                     states.REVOKED: 'magenta',
                     states.STARTED: 'yellow',
                     states.RETRY: 'orange',
                     'RECEIVED': 'blue'}
NODE_STATE_COLORS = {'ONLINE': 'green',
                     'OFFLINE': 'gray'}


class MonitorList(main_views.ChangeList):

    def __init__(self, *args, **kwargs):
        super(MonitorList, self).__init__(*args, **kwargs)
        self.title = self.model_admin.list_page_title


@display_field(_('state'), 'state')
def colored_state(task):
    state = escape(task.state)
    color = TASK_STATE_COLORS.get(task.state, 'black')
    return format_html(
        '<b><span style="color: {0};">{1}</span></b>', color, state
    )


@display_field(_('state'), 'last_heartbeat')
def node_state(node):
    state = node.is_alive() and 'ONLINE' or 'OFFLINE'
    color = NODE_STATE_COLORS[state]
    return format_html(
        '<b><span style="color: {0};">{1}</span></b>', color, state
    )


@display_field(_('ETA'), 'eta')
def eta(task):
    if not task.eta:
        return mark_safe('<span style="color: gray;">none</span>')
    return escape(make_aware(task.eta))


@display_field(_('when'), 'tstamp')
def tstamp(task):
    # convert to local timezone
    value = make_aware(task.tstamp)
    return format_html(
        '<div title="{0}">{1}</div>', str(value), naturaldate(value)
    )


@display_field(_('name'), 'name')
def name(task):
    short_name = abbrtask(task.name, 16)
    return format_html(
        '<div title="{0}"><b>{1}</b></div>', task.name, short_name
    )


class ModelMonitor(admin.ModelAdmin):
    can_add = False
    can_delete = False

    def get_changelist(self, request, **kwargs):
        return MonitorList

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context.setdefault('title', self.detail_title)
        return super(ModelMonitor, self).change_view(
            request, object_id, extra_context=extra_context,
        )

    def has_delete_permission(self, request, obj=None):
        if not self.can_delete:
            return False
        return super(ModelMonitor, self).has_delete_permission(request, obj)

    def has_add_permission(self, request):
        if not self.can_add:
            return False
        return super(ModelMonitor, self).has_add_permission(request)


class TaskMonitor(ModelMonitor):
    detail_title = _('Task detail')
    list_page_title = _('Tasks')
    rate_limit_confirmation_template = 'djcelery/confirm_rate_limit.html'
    date_hierarchy = 'tstamp'
    fieldsets = (
        (None, {
            'fields': ('state', 'task_id', 'name', 'args', 'kwargs',
                       'eta', 'runtime', 'worker', 'tstamp'),
            'classes': ('extrapretty', ),
        }),
        ('Details', {
            'classes': ('collapse', 'extrapretty'),
            'fields': ('result', 'traceback', 'expires'),
        }),
    )
    list_display = (
        fixedwidth('task_id', name=_('UUID'), pt=8),
        colored_state,
        name,
        fixedwidth('args', pretty=True),
        fixedwidth('kwargs', pretty=True),
        eta,
        tstamp,
        'worker',
    )
    readonly_fields = (
        'state', 'task_id', 'name', 'args', 'kwargs',
        'eta', 'runtime', 'worker', 'result', 'traceback',
        'expires', 'tstamp',
    )
    list_filter = ('state', 'name', 'tstamp', 'eta', 'worker')
    search_fields = ('name', 'task_id', 'args', 'kwargs', 'worker__hostname')
    actions = ['revoke_tasks',
               'terminate_tasks',
               'kill_tasks',
               'rate_limit_tasks']

    class Media:
        css = {'all': ('djcelery/style.css', )}

    @action(_('Revoke selected tasks'))
    def revoke_tasks(self, request, queryset):
        with current_app.default_connection() as connection:
            for state in queryset:
                revoke(state.task_id, connection=connection)

    @action(_('Terminate selected tasks'))
    def terminate_tasks(self, request, queryset):
        with current_app.default_connection() as connection:
            for state in queryset:
                revoke(state.task_id, connection=connection, terminate=True)

    @action(_('Kill selected tasks'))
    def kill_tasks(self, request, queryset):
        with current_app.default_connection() as connection:
            for state in queryset:
                revoke(state.task_id, connection=connection,
                       terminate=True, signal='KILL')

    @action(_('Rate limit selected tasks'))
    def rate_limit_tasks(self, request, queryset):
        tasks = set([task.name for task in queryset])
        opts = self.model._meta
        app_label = opts.app_label
        if request.POST.get('post'):
            rate = request.POST['rate_limit']
            with current_app.default_connection() as connection:
                for task_name in tasks:
                    rate_limit(task_name, rate, connection=connection)
            return None

        context = {
            'title': _('Rate limit selection'),
            'queryset': queryset,
            'object_name': force_str(opts.verbose_name),
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'opts': opts,
            'app_label': app_label,
        }

        return render(request, self.rate_limit_confirmation_template, context)

    def get_actions(self, request):
        actions = super(TaskMonitor, self).get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def get_queryset(self, request):
        qs = super(TaskMonitor, self).get_queryset(request)
        return qs.select_related('worker')


class WorkerMonitor(ModelMonitor):
    can_add = True
    detail_title = _('Node detail')
    list_page_title = _('Worker Nodes')
    list_display = ('hostname', node_state)
    readonly_fields = ('last_heartbeat', )
    actions = ['shutdown_nodes',
               'enable_events',
               'disable_events']

    @action(_('Shutdown selected worker nodes'))
    def shutdown_nodes(self, request, queryset):
        broadcast('shutdown', destination=[n.hostname for n in queryset])

    @action(_('Enable event mode for selected nodes.'))
    def enable_events(self, request, queryset):
        broadcast('enable_events',
                  destination=[n.hostname for n in queryset])

    @action(_('Disable event mode for selected nodes.'))
    def disable_events(self, request, queryset):
        broadcast('disable_events',
                  destination=[n.hostname for n in queryset])

    def get_actions(self, request):
        actions = super(WorkerMonitor, self).get_actions(request)
        actions.pop('delete_selected', None)
        return actions


admin.site.register(TaskState, TaskMonitor)
admin.site.register(WorkerState, WorkerMonitor)


# ### Periodic Tasks


class TaskSelectWidget(Select):
    celery_app = current_app
    _choices = None

    def tasks_as_choices(self):
        _ = self._modules  # noqa
        tasks = list(sorted(name for name in self.celery_app.tasks
                            if not name.startswith('celery.')))
        return (('', ''), ) + tuple(zip(tasks, tasks))

    @property
    def choices(self):
        if self._choices is None:
            self._choices = self.tasks_as_choices()
        return self._choices

    @choices.setter
    def choices(self, _):
        # ChoiceField.__init__ sets ``self.choices = choices``
        # which would override ours.
        pass

    @cached_property
    def _modules(self):
        self.celery_app.loader.import_default_modules()


class TaskChoiceField(forms.ChoiceField):
    widget = TaskSelectWidget

    def valid_value(self, value):
        return True


class PeriodicTaskForm(forms.ModelForm):
    regtask = TaskChoiceField(label=_('Task (registered)'),
                              required=False)
    task = forms.CharField(label=_('Task (custom)'), required=False,
                           max_length=200)

    class Meta:
        model = PeriodicTask
        exclude = ()

    def clean(self):
        data = super(PeriodicTaskForm, self).clean()
        regtask = data.get('regtask')
        if regtask:
            data['task'] = regtask
        if not data['task']:
            exc = forms.ValidationError(_('Need name of task'))
            self._errors['task'] = self.error_class(exc.messages)
            raise exc
        return data

    def _clean_json(self, field):
        value = self.cleaned_data[field]
        try:
            loads(value)
        except ValueError as exc:
            raise forms.ValidationError(
                _('Unable to parse JSON: %s') % exc,
            )
        return value

    def clean_args(self):
        return self._clean_json('args')

    def clean_kwargs(self):
        return self._clean_json('kwargs')


class PeriodicTaskAdmin(admin.ModelAdmin):
    form = PeriodicTaskForm
    model = PeriodicTask
    list_display = (
        'enabled',
        '__unicode__',
        'task',
        'args',
        'kwargs',
    )
    search_fields = ('name', 'task')
    list_display_links = ('enabled', '__unicode__', 'task')
    ordering = ('-enabled', 'name')
    fieldsets = (
        (None, {
            'fields': ('name', 'regtask', 'task', 'enabled'),
            'classes': ('extrapretty', 'wide'),
        }),
        ('Schedule', {
            'fields': ('interval', 'crontab'),
            'classes': ('extrapretty', 'wide', ),
        }),
        ('Arguments', {
            'fields': ('args', 'kwargs'),
            'classes': ('extrapretty', 'wide', 'collapse'),
        }),
        ('Execution Options', {
            'fields': ('expires', 'queue', 'exchange', 'routing_key'),
            'classes': ('extrapretty', 'wide', 'collapse'),
        }),
    )
    actions = ['enable_tasks',
               'disable_tasks']

    def update_periodic_tasks(self):
        dummy_periodic_task = PeriodicTask()
        dummy_periodic_task.no_changes = False
        PeriodicTasks.changed(dummy_periodic_task)

    @action(_('Enable selected periodic tasks'))
    def enable_tasks(self, request, queryset):
        queryset.update(enabled=True)
        self.update_periodic_tasks()

    @action(_('Disable selected periodic tasks'))
    def disable_tasks(self, request, queryset):
        queryset.update(enabled=False)
        self.update_periodic_tasks()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        scheduler = getattr(settings, 'CELERYBEAT_SCHEDULER', None)
        extra_context['wrong_scheduler'] = not is_database_scheduler(scheduler)
        return super(PeriodicTaskAdmin, self).changelist_view(request,
                                                              extra_context)

    def get_queryset(self, request):
        qs = super(PeriodicTaskAdmin, self).get_queryset(request)
        return qs.select_related('interval', 'crontab')


admin.site.register(IntervalSchedule)
admin.site.register(CrontabSchedule)
admin.site.register(PeriodicTask, PeriodicTaskAdmin)
