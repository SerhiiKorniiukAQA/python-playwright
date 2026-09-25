from playwright.sync_api import APIResponse

from api.base_api import BaseApi


class InvoicesApi(BaseApi):
    def get_invoices(self, token: str, page: int = 1) -> APIResponse:
        return self._send("GET", "/invoices", params={"page": page}, headers=self.auth_header(token))

    def get_invoice(self, invoice_id: str, token: str) -> APIResponse:
        return self._send("GET", f"/invoices/{invoice_id}", headers=self.auth_header(token))
