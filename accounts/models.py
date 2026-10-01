# -*- coding: utf-8 -*-
"""企业与账号领域（模块 M0 的登录/注册 + M1）。
企业主体、成员与角色、邀请、合作伙伴档案。

本模块由 ``<app>/models.py`` 按限界上下文拆分而来；
模型的 ``Meta.db_table`` 显式钉住历史物理表名
（``portal_*``），因此数据库结构、索引名与文档中的
表名清单保持不变。
"""

from django.conf import settings
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone
from core.models import Incoterm, TimeStampedModel
from catalog.models import Country, Currency, Industry


class Profile(models.Model):
    """账户扩展：参与者设置。

    阶段 1 实体“用户”的“界面语言”与“电话”属性，
    未包含在内置模型 ``User`` 中。
    """

    class Language(models.TextChoices):
        RU = "ru", "Русский"
        ZH = "zh", "中文"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="пользователь",
        on_delete=models.CASCADE, related_name="profile")
    language = models.CharField("язык интерфейса", max_length=2,
                                choices=Language.choices,
                                default=Language.RU)
    phone = models.CharField("телефон", max_length=24, blank=True,
                             validators=[RegexValidator(
                                 r"^\+?[\d\s-]{7,20}$",
                                 "Некорректный номер телефона")])

    class Meta:
        db_table = "portal_profile"
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        # 标签就是模型名称本身：在文档中该实体
        # 称为«Пользователь»（“用户”），面板用同一名称标注
        # 分区和面包屑。若为«Профиль»单独用词，
        # 就会在同一页面上与它们不一致。
        return (f"{self._meta.verbose_name.capitalize()}: "
                f"{self.user.get_username()}")


class Enterprise(TimeStampedModel):
    """贸易参与方（交易的俄方或中方）。"""

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        VERIFYING = "verifying", "На проверке"
        ACTIVE = "active", "Активна"
        BLOCKED = "blocked", "Заблокирована"

    name_ru = models.CharField("название (рус.)", max_length=128)
    name_zh = models.CharField("название (кит.)", max_length=128,
                               blank=True)
    country = models.ForeignKey(Country, verbose_name="страна",
                                on_delete=models.PROTECT,
                                related_name="enterprises")
    industry = models.ForeignKey(Industry, verbose_name="отрасль",
                                 on_delete=models.PROTECT, null=True,
                                 blank=True, related_name="enterprises")
    tin = models.CharField(
        "ИНН / код единой социальной лицензии", max_length=18, unique=True,
        validators=[MinLengthValidator(10)])
    address = models.CharField("адрес", max_length=256, blank=True)
    bank_account = models.CharField("банковский счёт", max_length=64,
                                    blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices, default=Status.NEW)

    class Meta:
        db_table = "portal_enterprise"
        verbose_name = "предприятие"
        verbose_name_plural = "предприятия"
        ordering = ["name_ru"]
        indexes = [models.Index(fields=["status", "country"])]

    def __str__(self):
        return self.name_ru


class Membership(models.Model):
    """“用户——企业——角色”关联。"""

    class Role(models.TextChoices):
        BUYER = "buyer", "Закупщик"
        SUPPLIER = "supplier", "Поставщик"
        LOGISTICS = "logistics", "Логист"
        BROKER = "broker", "Брокер"
        FINANCE = "finance", "Бухгалтер"
        ADMIN = "admin", "Администратор"

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name="пользователь",
                             on_delete=models.CASCADE,
                             related_name="memberships")
    enterprise = models.ForeignKey(Enterprise, verbose_name="предприятие",
                                   on_delete=models.CASCADE,
                                   related_name="members")
    role = models.CharField("роль", max_length=16,
                            choices=Role.choices, default=Role.BUYER)
    department = models.CharField("подразделение", max_length=64,
                                  blank=True)
    joined_at = models.DateField("дата вступления", default=timezone.now)
    is_active = models.BooleanField("активно", default=True)

    class Meta:
        db_table = "portal_membership"
        verbose_name = "членство"
        verbose_name_plural = "членства"
        ordering = ["enterprise", "role"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "enterprise"],
                name="membership_user_enterprise_unique"),
        ]

    def __str__(self):
        return f"{self.user.get_username()} @ {self.enterprise} ({self.role})"


class Invitation(models.Model):
    """邀请新参与者加入企业。"""

    class Status(models.TextChoices):
        PENDING = "pending", "Отправлено"
        ACCEPTED = "accepted", "Принято"
        EXPIRED = "expired", "Истекло"
        REVOKED = "revoked", "Отозвано"

    code = models.CharField("код приглашения", max_length=32, unique=True)
    email = models.EmailField("электронная почта")
    enterprise = models.ForeignKey(Enterprise, verbose_name="предприятие",
                                   on_delete=models.CASCADE,
                                   related_name="invitations")
    role = models.CharField("роль", max_length=16,
                            choices=Membership.Role.choices)
    valid_until = models.DateField("действительно до")
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.PENDING)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="пригласил",
        on_delete=models.SET_NULL, null=True, related_name="invitations_sent")
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        db_table = "portal_invitation"
        verbose_name = "приглашение"
        verbose_name_plural = "приглашения"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} → {self.enterprise}"

    @property
    def is_valid(self):
        return (self.status == self.Status.PENDING
                and self.valid_until >= timezone.now().date())


class Counterparty(models.Model):
    """企业已验证的合作伙伴（交易对手）。"""

    enterprise = models.ForeignKey(Enterprise,
                                   verbose_name="предприятие-инициатор",
                                   on_delete=models.CASCADE,
                                   related_name="counterparties")
    name = models.CharField("название партнёра", max_length=128)
    contact_person = models.CharField("контактное лицо", max_length=96,
                                      blank=True)
    phone = models.CharField("телефон", max_length=24, blank=True)
    default_currency = models.ForeignKey(
        Currency, verbose_name="валюта по умолчанию",
        on_delete=models.PROTECT, null=True, blank=True,
        related_name="counterparties")
    incoterm = models.CharField("базис поставки", max_length=3,
                                choices=Incoterm.choices,
                                default=Incoterm.FCA)
    note = models.TextField("примечание", blank=True)

    class Meta:
        db_table = "portal_counterparty"
        verbose_name = "контрагент"
        verbose_name_plural = "контрагенты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["enterprise", "name"],
                name="counterparty_enterprise_name_unique"),
        ]

    def __str__(self):
        return self.name

__all__ = [
    "Profile", "Enterprise", "Membership",
    "Invitation", "Counterparty",
]
