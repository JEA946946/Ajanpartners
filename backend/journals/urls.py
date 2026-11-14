from django.urls import path

from . import closing_views, lettrage, receipts, views

urlpatterns = [
    # Journal entries export — must be before <uuid:pk>
    path("journal-entries/export", views.journal_entries_export),
    # Journal Entries CRUD
    path("journal-entries", views.journal_entries_list_create),
    path("journal-entries/<uuid:pk>", views.journal_entries_detail),
    path("journal-entries/<uuid:pk>/post", views.journal_entry_post),
    path("journal-entries/<uuid:pk>/unpost", views.journal_entry_unpost),
    path("journal-entries/<uuid:pk>/reverse", closing_views.journal_entry_reverse),
    # Journals and month closing
    path("journals", closing_views.journals_list),
    path("journals/<int:pk>", closing_views.journals_detail),
    path("periods", closing_views.periods_list),
    path("periods/check", closing_views.period_check),
    path("periods/close", closing_views.period_close),
    # Tiers and lettrage
    path("tiers", lettrage.tiers_balances),
    path("tiers/lines", lettrage.tiers_lines),
    path("lettrage", lettrage.lettrage_create),
    path("lettrage/undo", lettrage.lettrage_undo),
    # Bank Statements
    path("bank-statements/upload", views.bank_statement_upload),
    path("bank-statements/auto-map", views.bank_statement_auto_map),
    path("bank-statements/confirm", views.bank_statement_confirm),
    path("bank-statements/history", views.bank_statement_history),
    # Bank Transactions
    path("bank-transactions/export", views.bank_transactions_export),
    path("bank-transactions", views.bank_transactions_list),
    # Incoming money matched to CRM invoices (journals/receipts.py)
    path("transactions/<uuid:jel_id>/invoice-suggestions", receipts.invoice_suggestions),
    path("transactions/<uuid:jel_id>/match-invoice", receipts.match_invoice),
    # Reports
    path("reports/trial-balance", views.report_trial_balance),
    path("reports/profit-and-loss", views.report_profit_and_loss),
    path("reports/balance-sheet", views.report_balance_sheet),
    # Margin Recognition & TVA
    path("margin-recognition/preview", views.margin_recognition_preview),
    path("margin-recognition/create", views.margin_recognition_create),
    # CMR Sync
    path("cmr/sync", views.cmr_sync),
    path("cmr/sync-audit", views.cmr_sync_audit),
    path("cmr/sync-contacts", views.cmr_sync_contacts),
    path("cmr/clients", views.cmr_clients_list),
    path("cmr/suppliers", views.cmr_suppliers_list),
    # Google Places proxy
    path("places/autocomplete", views.places_autocomplete),
    path("places/details", views.places_details),
]
