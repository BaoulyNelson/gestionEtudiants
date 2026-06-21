from django.views.generic import FormView, TemplateView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages as django_messages
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from .forms import FormulaireContact
from .models import MessageContact
from applications.articles.views import GestionnaireRequisMixin


def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')


class VueContact(FormView):
    template_name = 'contact/contact.html'
    form_class    = FormulaireContact
    success_url   = reverse_lazy('contact:succes')

    def form_valid(self, form):
        msg = form.save(commit=False)
        msg.ip_address = _get_ip(self.request)
        msg.save()
        try:
            send_mail(
                subject=f'[LeMédia] Nouveau message : {msg.get_sujet_display()}',
                message=f'De : {msg.nom} <{msg.email}>\n\n{msg.message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
        return super().form_valid(form)


class VueContactSucces(TemplateView):
    template_name = 'contact/succes.html'


class VueDashboardMessages(GestionnaireRequisMixin, ListView):
    template_name       = 'dashboard/messages/liste.html'
    context_object_name = 'messages_contact'
    paginate_by         = 20

    def get_queryset(self):
        return MessageContact.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['non_lus'] = MessageContact.objects.filter(is_read=False).count()
        return ctx


class VueLireMessage(GestionnaireRequisMixin, DetailView):
    template_name       = 'dashboard/messages/detail.html'
    context_object_name = 'msg'
    queryset            = MessageContact.objects.all()

    def get_object(self):
        obj = super().get_object()
        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=['is_read'])
        return obj
