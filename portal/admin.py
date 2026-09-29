# -*- coding: utf-8 -*-
"""Регистрация моделей приложения portal в административной панели.

Этап 3 («Модели приложения»). Приёмы демонстрации:

* ``list_display`` / ``list_filter`` / ``search_fields`` для типовых
  перечней;
* ``TabularInline`` для составных сущностей («документ — позиции»);
* групповая регистрация однотипных справочников одним классом.
"""

from django.contrib import admin

from . import models as m

admin.site.site_header = "Администрирование TradeHub"
admin.site.site_title = "TradeHub"
admin.site.index_title = "Раздел предметной области"


# ------------------------------------------------------- справочники

@admin.register(m.Country, m.Currency, m.Uom, m.GoodCategory,
                m.Industry, m.Tariff, m.SystemParam)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ("pk", "display",)
    search_fields = ("pk",)

    def display(self, obj):
        return str(obj)
    display.short_description = "значение"


@admin.register(m.BorderCrossing)
class BorderCrossingAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "mode", "country", "dwell_days")
    list_filter = ("mode", "country")
    search_fields = ("code", "name_ru", "name_zh")


@admin.register(m.TransportLane)
class TransportLaneAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "origin", "destination", "mode", "days")
    list_filter = ("mode",)
    search_fields = ("code", "name")


# ------------------------------------------- организации и пользователи

@admin.register(m.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "language", "phone")
    list_filter = ("language",)
    search_fields = ("user__username", "phone")


@admin.register(m.Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ("name_ru", "country", "tin", "status", "created_at")
    list_filter = ("status", "country")
    search_fields = ("name_ru", "name_zh", "tin")


@admin.register(m.Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "enterprise", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__username", "enterprise__name_ru")


@admin.register(m.Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "enterprise", "role", "valid_until", "status")
    list_filter = ("status", "role")
    search_fields = ("email", "code")


@admin.register(m.Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ("name", "enterprise", "contact_person", "incoterm")
    search_fields = ("name", "contact_person")


# -------------------------------------------------------- товары

class PackagingInline(admin.TabularInline):
    model = m.Packaging
    extra = 0


class ProductImageInline(admin.TabularInline):
    model = m.ProductImage
    extra = 0


@admin.register(m.Good)
class GoodAdmin(admin.ModelAdmin):
    list_display = ("sku", "name_ru", "category", "uom", "brand",
                    "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("sku", "name_ru", "name_zh", "hs_code")
    inlines = [PackagingInline, ProductImageInline]


@admin.register(m.Packaging)
class PackagingAdmin(admin.ModelAdmin):
    list_display = ("good", "kind", "units_per_pack", "unit_weight_kg")
    list_filter = ("kind",)


@admin.register(m.ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("good", "order", "is_main")


# --------------------------------------------- преддоговорные сущности

class RfqLineInline(admin.TabularInline):
    model = m.RfqLine
    extra = 0


@admin.register(m.Rfq)
class RfqAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "buyer", "due_date", "status")
    list_filter = ("status", "incoterm")
    search_fields = ("number", "title")
    inlines = [RfqLineInline]


class QuoteLineInline(admin.TabularInline):
    model = m.QuoteLine
    extra = 0


@admin.register(m.Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("number", "rfq", "supplier", "amount", "valid_until",
                    "status")
    list_filter = ("status",)
    search_fields = ("number",)
    inlines = [QuoteLineInline]


@admin.register(m.QuoteVersion)
class QuoteVersionAdmin(admin.ModelAdmin):
    list_display = ("quote", "version", "changed_fields", "author",
                    "created_at")


# --------------------------------------------------------- заказы

class OrderLineInline(admin.TabularInline):
    model = m.OrderLine
    extra = 0


@admin.register(m.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "buyer", "supplier", "amount", "status",
                    "signed_date")
    list_filter = ("status", "incoterm")
    search_fields = ("number",)
    inlines = [OrderLineInline]


@admin.register(m.OrderMilestone)
class OrderMilestoneAdmin(admin.ModelAdmin):
    list_display = ("order", "kind", "planned_date", "actual_date",
                    "status")
    list_filter = ("kind", "status")


@admin.register(m.OrderChange)
class OrderChangeAdmin(admin.ModelAdmin):
    list_display = ("order", "change_type", "initiated_by", "approved_by",
                    "created_at")
    list_filter = ("change_type",)


# --------------------------------------------------------- логистика

@admin.register(m.Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("number", "order", "qty", "ship_date", "container_no")
    search_fields = ("number", "container_no")


@admin.register(m.Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ("shipment", "carrier", "mode", "lane", "waybill_no",
                    "cost")
    list_filter = ("mode",)
    search_fields = ("waybill_no",)


@admin.register(m.TrackPoint)
class TrackPointAdmin(admin.ModelAdmin):
    list_display = ("transport", "event_time", "place", "status")


@admin.register(m.Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("number", "shipment", "kind", "severity", "status")
    list_filter = ("kind", "severity", "status")
    search_fields = ("number", "description")


# ----------------------------------------- документы и соответствие

@admin.register(m.DocType)
class DocTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "stage")
    list_filter = ("stage",)


@admin.register(m.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("doc_type", "order", "issuer", "issued_date",
                    "valid_until", "status")
    list_filter = ("status", "doc_type")
    date_hierarchy = "issued_date"


@admin.register(m.Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("number", "kind", "good", "valid_until", "fgis_no")
    list_filter = ("kind",)
    search_fields = ("number", "fgis_no")


@admin.register(m.DocRequirement)
class DocRequirementAdmin(admin.ModelAdmin):
    list_display = ("order", "doc_type", "status")
    list_filter = ("status",)


@admin.register(m.ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ("order", "result", "checker", "checked_at")
    list_filter = ("result",)


@admin.register(m.DeadlineReminder)
class DeadlineReminderAdmin(admin.ModelAdmin):
    list_display = ("target_kind", "target_id", "due_date", "recipient",
                    "status")
    list_filter = ("status", "target_kind")


# --------------------------------------------------------- коммуникация

@admin.register(m.Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = ("subject_kind", "subject_label", "status",
                    "last_message_at")
    list_filter = ("subject_kind", "status")


@admin.register(m.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("dialog", "author", "language", "created_at")
    list_filter = ("language",)
    search_fields = ("body",)


@admin.register(m.Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ("message", "source_language", "target_language",
                    "engine", "created_at")


@admin.register(m.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("owner_kind", "owner_id", "size_bytes", "mime_type",
                    "created_at")


# ------------------------------- задачи, уведомления, аналитика, счета

@admin.register(m.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "assignee", "due_date", "priority",
                    "status")
    list_filter = ("status", "priority", "source_kind")
    search_fields = ("number", "title")


@admin.register(m.TaskReminder)
class TaskReminderAdmin(admin.ModelAdmin):
    list_display = ("task", "channel", "send_at", "is_sent")
    list_filter = ("channel", "is_sent")


@admin.register(m.NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "channel", "is_enabled")
    list_filter = ("channel", "is_enabled")


@admin.register(m.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "kind", "title", "is_read", "created_at")
    list_filter = ("kind", "is_read")
    search_fields = ("title",)


@admin.register(m.Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "unit", "period")


@admin.register(m.MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ("metric", "period_key", "value", "calculated_at")


@admin.register(m.ComplianceRisk)
class ComplianceRiskAdmin(admin.ModelAdmin):
    list_display = ("order", "kind", "probability", "impact", "level")
    list_filter = ("level",)


class StatementLineInline(admin.TabularInline):
    model = m.StatementLine
    extra = 0


@admin.register(m.Statement)
class StatementAdmin(admin.ModelAdmin):
    list_display = ("number", "order", "amount", "due_date", "status")
    list_filter = ("status",)
    inlines = [StatementLineInline]


@admin.register(m.Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = ("order", "partner", "period", "our_amount",
                    "partner_amount", "diff", "status")
    list_filter = ("status",)


@admin.register(m.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("statement", "paid_date", "amount", "buyer_confirmed",
                    "supplier_confirmed")


# ------------------------------------------------------- системные

@admin.register(m.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_kind",
                    "target_id")
    list_filter = ("action", "target_kind")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
