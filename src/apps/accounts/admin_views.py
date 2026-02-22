from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy


class AdminForcePasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("admin:index")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if getattr(user, "must_change_password", False):
            user.must_change_password = False
            user.save(update_fields=["must_change_password"])
        messages.success(self.request, "Senha alterada com sucesso.")
        return response
