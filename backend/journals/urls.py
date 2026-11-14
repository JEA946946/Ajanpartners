from django.urls import path

from . import closing_views, lettrage, reports, views

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
    # Årsafslutning (journals/closing.py)
    path("year-end/status", closing_views.year_end_status),
    path("year-end/check", closing_views.year_end_check),
    path("year-end/close", closing_views.year_end_close),
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
    # Reports
    path("reports/trial-balance", reports.report_trial_balance),
    path("reports/profit-and-loss", reports.report_profit_and_loss),
    path("reports/balance-sheet", reports.report_balance_sheet),
    path("reports/account-card", reports.report_account_card),
    # Google Places proxy
    path("places/autocomplete", views.places_autocomplete),
    path("places/details", views.places_details),
]
