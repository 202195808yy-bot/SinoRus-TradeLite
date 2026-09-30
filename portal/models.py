# -*- coding: utf-8 -*-
"""Модели приложения курсового проекта «TradeHub».

Этап 3 («Модели приложения»). Сущности взяты из перечня предметной
области этапа 1 (56 сущностей, 9 классов); 52 из них реализованы
отдельными моделями, четыре — полями, словарями значений или
встроенной моделью ``django.contrib.auth.models.User`` (таблица
соответствия приведена в пояснительной записке):

* «Характеристика товара» — JSON-поле ``Good.attributes``;
* «Роль» — словарь ``Membership.Role``;
* «Файл (медиа)» — ``FileField`` моделей и модель ``Attachment``;
* «Термин глоссария» — статический справочник интерфейса (этап 4).

Соглашения:

* ``TimeStampedModel`` — общие поля временных отметок;
* номера документов формируются в ``save()`` по шаблону
  ``ПРЕФИКС-ГГГГ-NNNN``;
* суммы и количества — ``DecimalField`` (без ошибок представлений);
* ограничения целостности — ``UniqueConstraint`` и ``CheckConstraint``;
* ``verbose_name`` на русском языке — источник для админ-панели и
  перечня полей в пояснительной записке.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import (
    MinLengthValidator, RegexValidator,
)
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .i18n import label


# ======================================================================
# Вспомогательные классы и словари значений
# ======================================================================

class TimeStampedModel(models.Model):
    """Абстрактная модель с отметками создания и изменения записи."""

    created_at = models.DateTimeField("создано", auto_now_add=True)
    updated_at = models.DateTimeField("обновлено", auto_now=True)

    class Meta:
        abstract = True


class DocNumberMixin:
    """Генерация номера вида ``ПРЕФИКС-ГГГГ-NNNN`` при первом сохранении."""

    number_prefix = "DOC"

    def generate_number(self):
        year = timezone.now().year
        seq = type(self).objects.count() + 1
        return f"{self.number_prefix}-{year:04d}-{seq:04d}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)


class Incoterm(models.TextChoices):
    EXW = "EXW", "EXW"
    FCA = "FCA", "FCA"
    CPT = "CPT", "CPT"
    CIF = "CIF", "CIF"
    DAP = "DAP", "DAP"
    DDP = "DDP", "DDP"


class TransportMode(models.TextChoices):
    ROAD = "road", "Автомобильный"
    RAIL = "rail", "Железнодорожный"
    SEA = "sea", "Морской"
    AIR = "air", "Воздушный"


# ======================================================================
# Класс «С»: справочные и словарные сущности
# ======================================================================

class Currency(models.Model):
    """Справочник валют."""

    code = models.CharField("код", max_length=3, unique=True,
                            validators=[RegexValidator(r"^[A-Z]{3}$")])
    name_ru = models.CharField("название (рус.)", max_length=64)
    name_zh = models.CharField("название (кит.)", max_length=64)
    symbol = models.CharField("символ", max_length=4)
    decimals = models.PositiveSmallIntegerField("знаков после запятой",
                                                default=2)

    class Meta:
        verbose_name = "валюта"
        verbose_name_plural = "валюты"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.symbol})"


class Country(models.Model):
    """Справочник стран-участниц торговли."""

    code2 = models.CharField("код ISO 3166-1 alpha-2", max_length=2,
                             unique=True)
    name_ru = models.CharField("название (рус.)", max_length=64)
    name_zh = models.CharField("название (кит.)", max_length=64)
    currency = models.ForeignKey(Currency, verbose_name="основная валюта",
                                 on_delete=models.PROTECT, null=True,
                                 blank=True, related_name="countries")
    timezone = models.CharField("часовой пояс", max_length=32,
                                default="Asia/Shanghai")

    class Meta:
        verbose_name = "страна"
        verbose_name_plural = "страны"
        ordering = ["code2"]

    def __str__(self):
        return f"{self.code2} — {self.name_ru}"


class Uom(models.Model):
    """Единицы измерения товаров."""

    class Kind(models.TextChoices):
        COUNT = "count", "Штуки"
        WEIGHT = "weight", "Масса"
        VOLUME = "volume", "Объём"

    code = models.CharField("код", max_length=8, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=32)
    name_zh = models.CharField("название (кит.)", max_length=32)
    kind = models.CharField("тип", max_length=8, choices=Kind.choices,
                            default=Kind.COUNT)

    class Meta:
        verbose_name = "единица измерения"
        verbose_name_plural = "единицы измерения"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name_ru} ({self.code})"


class GoodCategory(models.Model):
    """Иерархический справочник категорий товаров."""

    code = models.CharField("код", max_length=16, unique=True)
    parent = models.ForeignKey("self", verbose_name="родительская категория",
                               on_delete=models.PROTECT, null=True,
                               blank=True, related_name="children")
    name_ru = models.CharField("название (рус.)", max_length=96)
    name_zh = models.CharField("название (кит.)", max_length=96)
    level = models.PositiveSmallIntegerField("уровень вложенности", default=1)

    class Meta:
        verbose_name = "категория товара"
        verbose_name_plural = "категории товаров"
        ordering = ["code"]
        constraints = [
            models.CheckConstraint(
                check=Q(level__gte=1, level__lte=3),
                name="goodcategory_level_1_3"),
        ]

    def __str__(self):
        return f"{self.code} — {self.name_ru}"


class Industry(models.Model):
    """Справочник отраслей промышленности."""

    code = models.CharField("код", max_length=16, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=96)
    name_zh = models.CharField("название (кит.)", max_length=96)

    class Meta:
        verbose_name = "отрасль"
        verbose_name_plural = "отрасли"
        ordering = ["code"]

    def __str__(self):
        return self.name_ru


class BorderCrossing(models.Model):
    """Таможенный пункт пропуска."""

    code = models.CharField("код", max_length=16, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=96)
    name_zh = models.CharField("название (кит.)", max_length=96)
    mode = models.CharField("вид транспорта", max_length=8,
                            choices=TransportMode.choices,
                            default=TransportMode.ROAD)
    country = models.ForeignKey(Country, verbose_name="страна",
                                on_delete=models.PROTECT,
                                related_name="crossings")
    capacity_t_per_day = models.DecimalField(
        "пропускная способность, т/сут", max_digits=9, decimal_places=1,
        null=True, blank=True)
    dwell_days = models.DecimalField(
        "среднее время пребывания, сут", max_digits=4, decimal_places=1,
        null=True, blank=True)

    class Meta:
        verbose_name = "пункт пропуска"
        verbose_name_plural = "пункты пропуска"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name_ru}"


class TransportLane(models.Model):
    """Логистический канал между двумя пунктами пропуска."""

    code = models.CharField("код", max_length=16, unique=True)
    name = models.CharField("название", max_length=128)
    origin = models.ForeignKey(BorderCrossing,
                               verbose_name="пункт отправления",
                               on_delete=models.PROTECT,
                               related_name="lanes_from")
    destination = models.ForeignKey(
        BorderCrossing, verbose_name="пункт назначения",
        on_delete=models.PROTECT, related_name="lanes_to")
    mode = models.CharField("вид транспорта", max_length=8,
                            choices=TransportMode.choices,
                            default=TransportMode.ROAD)
    days = models.DecimalField("сроки доставки, сут", max_digits=5,
                               decimal_places=1)
    price_per_kg = models.DecimalField(
        "стоимость, за кг", max_digits=9, decimal_places=2,
        null=True, blank=True)

    class Meta:
        verbose_name = "логистический канал"
        verbose_name_plural = "логистические каналы"
        ordering = ["code"]
        constraints = [
            models.CheckConstraint(
                check=~Q(origin=models.F("destination")),
                name="lane_origin_differs_destination"),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Tariff(models.Model):
    """Таможенный тариф по коду ТН ВЭД."""

    hs_code = models.CharField("код ТН ВЭД", max_length=12, unique=True,
                               validators=[RegexValidator(r"^\d{4,12}$")])
    duty_rate = models.DecimalField(
        "пошлина, %", max_digits=5, decimal_places=2)
    vat_rate = models.DecimalField(
        "НДС, %", max_digits=5, decimal_places=2)
    valid_from = models.DateField("действует с")

    class Meta:
        verbose_name = "таможенный тариф"
        verbose_name_plural = "таможенные тарифы"
        ordering = ["hs_code"]

    def __str__(self):
        return (f"{self.hs_code}: {label('пошлина')} {self.duty_rate}%,"
                f" {label('НДС')} {self.vat_rate}%")


# ======================================================================
# Класс «O»: организации и пользователи
# ======================================================================

class Profile(models.Model):
    """Расширение учётной записи: настройки участника.

    Атрибуты «язык интерфейса» и «телефон» сущности «Пользователь»
    этапа 1, не входящие во встроенную модель ``User``.
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
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        # Подпись — само название модели: в документах эта сущность
        # называется «Пользователь» («用户»), и панель подписывает ею же
        # раздел и хлебные крошки. Отдельное слово для «Профиль» разошлось
        # бы с ними на одной и той же странице.
        return (f"{self._meta.verbose_name.capitalize()}: "
                f"{self.user.get_username()}")


class Enterprise(TimeStampedModel):
    """Участник торговли (российская или китайская сторона сделки)."""

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
        verbose_name = "предприятие"
        verbose_name_plural = "предприятия"
        ordering = ["name_ru"]
        indexes = [models.Index(fields=["status", "country"])]

    def __str__(self):
        return self.name_ru


class Membership(models.Model):
    """Связь «пользователь — предприятие — роль»."""

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
    """Приглашение нового участника в предприятие."""

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
    """Проверенный партнёр (контрагент) предприятия."""

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


# ======================================================================
# Класс «T»: товарная номенклатура
# ======================================================================

class Good(TimeStampedModel):
    """Карточка товара.

    Сущность «Характеристика товара» этапа 1 реализована JSON-полем
    ``attributes``; упаковка — отдельной моделью :class:`Packaging`.
    """

    sku = models.CharField("артикул (SKU)", max_length=32, unique=True,
                           validators=[RegexValidator(
                               r"^[A-Z0-9][A-Z0-9-]{2,31}$",
                               "Артикул: заглавные буквы, цифры и дефис")])
    hs_code = models.CharField("код ТН ВЭД", max_length=12, blank=True,
                               validators=[RegexValidator(
                                   r"^\d{4,12}$", "Только цифры")])
    name_ru = models.CharField("название (рус.)", max_length=191)
    name_zh = models.CharField("название (кит.)", max_length=191)
    category = models.ForeignKey(GoodCategory,
                                 verbose_name="категория",
                                 on_delete=models.PROTECT,
                                 related_name="goods")
    uom = models.ForeignKey(Uom, verbose_name="единица измерения",
                            on_delete=models.PROTECT,
                            related_name="goods")
    brand = models.CharField("торговая марка", max_length=64, blank=True)
    shelf_life_days = models.PositiveIntegerField(
        "срок хранения, сут", null=True, blank=True)
    attributes = models.JSONField(
        "характеристики", default=dict, blank=True,
        help_text="Например: {\"Мощность\": \"150 Вт\"}")
    description_ru = models.TextField("описание (рус.)", blank=True)
    description_zh = models.TextField("описание (кит.)", blank=True)
    is_active = models.BooleanField("в каталоге", default=True)

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["sku"]
        indexes = [models.Index(fields=["category", "is_active"])]

    def __str__(self):
        return f"{self.sku} — {self.name_ru}"


class Packaging(models.Model):
    """Вариант упаковки товара."""

    class Kind(models.TextChoices):
        BOX = "box", "Коробка"
        PALLET = "pallet", "Паллет"
        BAG = "bag", "Мешок"
        CONTAINER = "container", "Контейнер"

    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.CASCADE,
                             related_name="packagings")
    kind = models.CharField("тип упаковки", max_length=16,
                            choices=Kind.choices, default=Kind.BOX)
    units_per_pack = models.PositiveIntegerField("штук в упаковке",
                                                 default=1)
    unit_weight_kg = models.DecimalField(
        "масса места, кг", max_digits=10, decimal_places=3,
        null=True, blank=True)
    dims = models.CharField("габариты (ДхШхВ), см", max_length=32,
                            blank=True)

    class Meta:
        verbose_name = "упаковка"
        verbose_name_plural = "упаковки"
        ordering = ["good", "kind"]
        constraints = [
            models.CheckConstraint(
                check=Q(units_per_pack__gte=1),
                name="packaging_units_positive"),
        ]

    def __str__(self):
        return f"{self.good.sku}: {self.get_kind_display()}"


class ProductImage(models.Model):
    """Изображение товара в карточке."""

    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.CASCADE,
                             related_name="images")
    file = models.FileField("файл", upload_to="goods/%Y/%m")
    order = models.PositiveSmallIntegerField("порядок", default=0)
    is_main = models.BooleanField("главное изображение", default=False)

    class Meta:
        verbose_name = "изображение товара"
        verbose_name_plural = "изображения товаров"
        ordering = ["good", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["good"], condition=Q(is_main=True),
                name="productimage_single_main"),
        ]

    def __str__(self):
        return f"{self.good.sku} #{self.order}"


# ======================================================================
# Класс «R»: преддоговорные сущности
# ======================================================================

class Rfq(DocNumberMixin, TimeStampedModel):
    """Запрос котировки (RFQ), который создаёт закупщик."""

    number_prefix = "RFQ"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        SENT = "sent", "Опубликован"
        QUOTED = "quoted", "Есть предложения"
        CLOSED = "closed", "Закрыт"
        CANCELED = "canceled", "Отменён"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    buyer = models.ForeignKey(Enterprise, verbose_name="закупщик",
                              on_delete=models.PROTECT,
                              related_name="rfqs")
    title = models.CharField("заголовок", max_length=191)
    due_date = models.DateField("срок ответа")
    incoterm = models.CharField("базис поставки", max_length=3,
                                choices=Incoterm.choices,
                                default=Incoterm.FCA)
    currency = models.ForeignKey(Currency, verbose_name="валюта",
                                 on_delete=models.PROTECT,
                                 related_name="rfqs")
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.DRAFT)
    comment = models.TextField("комментарий", blank=True)

    class Meta:
        verbose_name = "запрос котировки"
        verbose_name_plural = "запросы котировки"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self):
        return f"{self.number}: {self.title}"

    @property
    def is_overdue(self):
        return (self.status in (self.Status.SENT, self.Status.QUOTED)
                and self.due_date < timezone.now().date())


class RfqLine(models.Model):
    """Позиция запроса котировки."""

    rfq = models.ForeignKey(Rfq, verbose_name="запрос",
                            on_delete=models.CASCADE, related_name="lines")
    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.PROTECT,
                             related_name="rfq_lines")
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3)
    target_price = models.DecimalField(
        "целевая цена", max_digits=12, decimal_places=2,
        null=True, blank=True)
    requirement = models.CharField("требование", max_length=191,
                                   blank=True)

    class Meta:
        verbose_name = "позиция запроса"
        verbose_name_plural = "позиции запросов"
        ordering = ["rfq", "pk"]
        constraints = [
            models.CheckConstraint(check=Q(qty__gt=Decimal("0")),
                                   name="rfqline_qty_positive"),
        ]

    def __str__(self):
        return f"#{self.pk}: {self.good} × {self.qty}"


class Quote(DocNumberMixin, TimeStampedModel):
    """Предложение поставщика на запрос котировки."""

    number_prefix = "QUO"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        SENT = "sent", "Отправлено"
        ACCEPTED = "accepted", "Принято"
        REJECTED = "rejected", "Отклонено"
        EXPIRED = "expired", "Истекло"
        WITHDRAWN = "withdrawn", "Отозвано"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    rfq = models.ForeignKey(Rfq, verbose_name="запрос",
                            on_delete=models.PROTECT, related_name="quotes")
    supplier = models.ForeignKey(Enterprise, verbose_name="поставщик",
                                 on_delete=models.PROTECT,
                                 related_name="quotes")
    valid_until = models.DateField("действительно до")
    incoterm = models.CharField("базис поставки", max_length=3,
                                choices=Incoterm.choices)
    currency = models.ForeignKey(Currency, verbose_name="валюта",
                                 on_delete=models.PROTECT,
                                 related_name="quotes")
    amount = models.DecimalField("сумма", max_digits=14, decimal_places=2,
                                 default=Decimal("0"))
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.DRAFT)
    comment = models.TextField("комментарий", blank=True)

    class Meta:
        verbose_name = "предложение"
        verbose_name_plural = "предложения"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "valid_until"])]
        constraints = [
            models.CheckConstraint(check=Q(amount__gte=Decimal("0")),
                                   name="quote_amount_non_negative"),
        ]

    def __str__(self):
        return f"{self.number} ({self.supplier})"

    @property
    def is_valid(self):
        return (self.status == self.Status.SENT
                and self.valid_until >= timezone.now().date())


class QuoteLine(models.Model):
    """Позиция предложения."""

    quote = models.ForeignKey(Quote, verbose_name="предложение",
                              on_delete=models.CASCADE,
                              related_name="lines")
    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.PROTECT,
                             related_name="quote_lines")
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3)
    price = models.DecimalField("цена", max_digits=12, decimal_places=2)
    delivery_days = models.PositiveSmallIntegerField(
        "срок поставки, сут", null=True, blank=True)

    class Meta:
        verbose_name = "позиция предложения"
        verbose_name_plural = "позиции предложений"
        ordering = ["quote", "pk"]
        constraints = [
            models.CheckConstraint(
                check=Q(qty__gt=Decimal("0"), price__gte=Decimal("0")),
                name="quoteline_values_positive"),
        ]

    @property
    def amount(self):
        return (self.qty * self.price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"#{self.pk}: {self.good}"


class QuoteVersion(models.Model):
    """Версия предложения с фиксацией изменённых условий."""

    quote = models.ForeignKey(Quote, verbose_name="предложение",
                              on_delete=models.CASCADE,
                              related_name="versions")
    version = models.PositiveSmallIntegerField("номер версии", default=1)
    changed_fields = models.CharField("изменённые поля", max_length=191,
                                      blank=True)
    comment = models.CharField("пояснение", max_length=256, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name="изменил",
                               on_delete=models.SET_NULL, null=True,
                               related_name="quote_versions")
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        verbose_name = "версия предложения"
        verbose_name_plural = "версии предложений"
        ordering = ["quote", "version"]
        constraints = [
            models.UniqueConstraint(fields=["quote", "version"],
                                    name="quoteversion_unique"),
        ]

    def __str__(self):
        return f"{self.quote.number} v{self.version}"


# ======================================================================
# Класс «Z»: заказ и исполнение
# ======================================================================

class Order(DocNumberMixin, TimeStampedModel):
    """Подтверждённая сделка — ядро предметной области."""

    number_prefix = "ORD"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        CONFIRMED = "confirmed", "Подписан"
        IN_PRODUCTION = "in_production", "Производство"
        SHIPPED = "shipped", "Отгружен"
        COMPLETED = "completed", "Завершён"
        CANCELED = "canceled", "Отменён"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    buyer = models.ForeignKey(Enterprise, verbose_name="закупщик",
                              on_delete=models.PROTECT,
                              related_name="orders_as_buyer")
    supplier = models.ForeignKey(Enterprise, verbose_name="поставщик",
                                 on_delete=models.PROTECT,
                                 related_name="orders_as_supplier")
    quote = models.ForeignKey(Quote, verbose_name="предложение",
                              on_delete=models.PROTECT,
                              related_name="orders")
    incoterm = models.CharField("базис поставки", max_length=3,
                                choices=Incoterm.choices)
    currency = models.ForeignKey(Currency, verbose_name="валюта",
                                 on_delete=models.PROTECT,
                                 related_name="orders")
    amount = models.DecimalField("сумма", max_digits=14, decimal_places=2)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.DRAFT)
    signed_date = models.DateField("дата подписания", null=True, blank=True)

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]
        constraints = [
            models.CheckConstraint(
                check=~Q(buyer=models.F("supplier")),
                name="order_buyer_differs_supplier"),
            models.CheckConstraint(
                check=Q(amount__gte=Decimal("0")),
                name="order_amount_non_negative"),
        ]

    def __str__(self):
        return f"{self.number}: {self.supplier} → {self.buyer}"

    @property
    def shipped_share(self):
        """Доля отгруженных партий в общем количестве заказа."""
        total = sum(line.qty for line in self.lines.all())
        if not total:
            return Decimal("0")
        shipped = sum(sh.qty for sh in self.shipments.all())
        return (shipped / total).quantize(Decimal("0.001"))


class OrderLine(models.Model):
    """Позиция заказа."""

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="lines")
    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.PROTECT,
                             related_name="order_lines")
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3)
    price = models.DecimalField("цена", max_digits=12, decimal_places=2)
    delivery_days = models.PositiveSmallIntegerField(
        "срок поставки, сут", null=True, blank=True)

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказов"
        ordering = ["order", "pk"]
        constraints = [
            models.CheckConstraint(
                check=Q(qty__gt=Decimal("0"), price__gte=Decimal("0")),
                name="orderline_values_positive"),
        ]

    @property
    def amount(self):
        return (self.qty * self.price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"#{self.pk}: {self.good}"


class OrderMilestone(models.Model):
    """Этап (веха) исполнения заказа."""

    class Kind(models.TextChoices):
        CONTRACT = "contract", "Подписание"
        PREPAYMENT = "prepayment", "Предоплата"
        PRODUCTION = "production", "Производство"
        PACKING = "packing", "Упаковка"
        SHIPMENT = "shipment", "Отгрузка"
        CUSTOMS = "customs", "Таможня"
        DELIVERY = "delivery", "Передача"
        PAYMENT = "payment", "Расчёт"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        DONE = "done", "Выполнен"
        SKIPPED = "skipped", "Пропущен"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="milestones")
    kind = models.CharField("вид этапа", max_length=16,
                            choices=Kind.choices)
    planned_date = models.DateField("плановая дата")
    actual_date = models.DateField("фактическая дата", null=True, blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.PENDING)
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ответственный",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="milestones")

    class Meta:
        verbose_name = "этап заказа"
        verbose_name_plural = "этапы заказов"
        ordering = ["order", "planned_date"]
        constraints = [
            models.UniqueConstraint(fields=["order", "kind"],
                                    name="milestone_order_kind_unique"),
        ]

    def __str__(self):
        return f"{self.order.number}: {self.get_kind_display()}"


class OrderChange(models.Model):
    """Зафиксированное изменение условий заказа."""

    class ChangeType(models.TextChoices):
        SCOPE = "scope", "Состав"
        DATES = "dates", "Сроки"
        PRICE = "price", "Цена"
        ADDRESS = "address", "Адрес"
        OTHER = "other", "Прочее"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="changes")
    change_type = models.CharField("тип изменения", max_length=16,
                                   choices=ChangeType.choices)
    before = models.TextField("было", blank=True)
    after = models.TextField("стало", blank=True)
    reason = models.TextField("причина", blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="инициатор",
        on_delete=models.SET_NULL, null=True, related_name="changes_init")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="согласовал",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="changes_approved")
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        verbose_name = "изменение заказа"
        verbose_name_plural = "изменения заказов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.number}: {self.get_change_type_display()}"


# ======================================================================
# Класс «Z»: логистика
# ======================================================================

class Shipment(DocNumberMixin, TimeStampedModel):
    """Партия (отгрузка) в рамках заказа."""

    number_prefix = "SHP"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.PROTECT,
                              related_name="shipments")
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3)
    weight_kg = models.DecimalField("масса, кг", max_digits=12,
                                    decimal_places=2, null=True, blank=True)
    volume_m3 = models.DecimalField(
        "объём, м³", max_digits=12, decimal_places=3, null=True, blank=True)
    ship_date = models.DateField("дата отгрузки", null=True, blank=True)
    container_no = models.CharField(
        "номер контейнера", max_length=16, blank=True)

    class Meta:
        verbose_name = "партия"
        verbose_name_plural = "партии"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} ({self.order.number})"


class Transport(models.Model):
    """Перевозка партии: перевозчик, канал, документы."""

    shipment = models.OneToOneField(
        Shipment, verbose_name="партия", on_delete=models.CASCADE,
        related_name="transport")
    carrier = models.ForeignKey(
        Enterprise, verbose_name="перевозчик", on_delete=models.PROTECT,
        null=True, blank=True, related_name="transports")
    carrier_name = models.CharField(
        "название перевозчика", max_length=128, blank=True,
        help_text="Заполняется, если перевозчик не зарегистрирован")
    mode = models.CharField("вид транспорта", max_length=8,
                            choices=TransportMode.choices,
                            default=TransportMode.ROAD)
    lane = models.ForeignKey(TransportLane, verbose_name="канал",
                             on_delete=models.PROTECT, null=True, blank=True,
                             related_name="transports")
    waybill_no = models.CharField("транспортная накладная", max_length=32,
                                  blank=True)
    cost = models.DecimalField("стоимость перевозки", max_digits=12,
                               decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "перевозка"
        verbose_name_plural = "перевозки"

    def __str__(self):
        who = self.carrier or self.carrier_name or "—"
        return f"{self.shipment.number}: {who}"


class TrackPoint(models.Model):
    """Точка маршрута перевозки (элемент отслеживания)."""

    transport = models.ForeignKey(Transport, verbose_name="перевозка",
                                  on_delete=models.CASCADE,
                                  related_name="track_points")
    event_time = models.DateTimeField("время события")
    place = models.CharField("место", max_length=128)
    status = models.CharField("статус", max_length=64)
    note = models.CharField("примечание", max_length=191, blank=True)

    class Meta:
        verbose_name = "точка маршрута"
        verbose_name_plural = "точки маршрута"
        ordering = ["transport", "event_time"]

    def __str__(self):
        return f"{self.place}: {self.status}"


class Incident(DocNumberMixin, TimeStampedModel):
    """Негативное отклонение по партии (инцидент)."""

    number_prefix = "INC"

    class Kind(models.TextChoices):
        DELAY = "delay", "Просрочка"
        DAMAGE = "damage", "Повреждение"
        SHORTAGE = "shortage", "Недовоз"
        CUSTOMS = "customs", "Таможня"
        OTHER = "other", "Прочее"

    class Severity(models.TextChoices):
        LOW = "low", "Низкая"
        MEDIUM = "medium", "Средняя"
        HIGH = "high", "Высокая"
        CRITICAL = "critical", "Критическая"

    class Status(models.TextChoices):
        REGISTERED = "registered", "Зарегистрирован"
        IN_PROGRESS = "in_progress", "В работе"
        RESOLVED = "resolved", "Урегулирован"
        CLOSED = "closed", "Закрыт"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    shipment = models.ForeignKey(Shipment, verbose_name="партия",
                                 on_delete=models.PROTECT,
                                 related_name="incidents")
    kind = models.CharField("тип", max_length=16, choices=Kind.choices)
    severity = models.CharField("критичность", max_length=8,
                                choices=Severity.choices,
                                default=Severity.MEDIUM)
    description = models.TextField("описание")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="заявитель",
        on_delete=models.SET_NULL, null=True, related_name="incidents")
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.REGISTERED)
    resolution = models.TextField("результат", blank=True)

    class Meta:
        verbose_name = "инцидент"
        verbose_name_plural = "инциденты"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "severity"])]

    def __str__(self):
        return f"{self.number}: {self.get_kind_display()}"


# ======================================================================
# Класс «D»: документооборот и соответствие
# ======================================================================

class DocType(models.Model):
    """Справочник видов документов."""

    class Stage(models.TextChoices):
        ORDER = "order", "Заказ"
        PRODUCTION = "production", "Производство"
        SHIPMENT = "shipment", "Отгрузка"
        CUSTOMS = "customs", "Таможня"
        PAYMENT = "payment", "Расчёт"

    code = models.CharField("код", max_length=16, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=128)
    name_zh = models.CharField("название (кит.)", max_length=128)
    stage = models.CharField("обязателен на этапе", max_length=16,
                             choices=Stage.choices)

    class Meta:
        verbose_name = "тип документа"
        verbose_name_plural = "типы документов"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name_ru}"


class Document(TimeStampedModel):
    """Документ сделки (инвойс, коносамент и т. п.)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        SIGNED = "signed", "Подписан"
        UPLOADED = "uploaded", "Загружен"
        ARCHIVED = "archived", "В архиве"
        EXPIRED = "expired", "Просрочен"

    doc_type = models.ForeignKey(DocType, verbose_name="тип документа",
                                 on_delete=models.PROTECT,
                                 related_name="documents")
    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.PROTECT, null=True, blank=True,
                              related_name="documents")
    shipment = models.ForeignKey(Shipment, verbose_name="партия",
                                 on_delete=models.PROTECT, null=True,
                                 blank=True, related_name="documents")
    file = models.FileField("файл", upload_to="docs/%Y/%m")
    issuer = models.CharField("кем выдан", max_length=128, blank=True)
    issued_date = models.DateField("дата выдачи")
    valid_until = models.DateField("действителен до", null=True, blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.UPLOADED)

    class Meta:
        verbose_name = "документ"
        verbose_name_plural = "документы"
        ordering = ["-issued_date"]
        indexes = [models.Index(fields=["status", "valid_until"])]
        constraints = [
            models.CheckConstraint(
                check=Q(valid_until__isnull=True)
                      | Q(valid_until__gte=models.F("issued_date")),
                name="document_validity_not_inverted"),
        ]

    def __str__(self):
        return f"{self.doc_type.code} ({self.issued_date})"


class Certificate(TimeStampedModel):
    """Разрешительный документ / сертификат."""

    class Kind(models.TextChoices):
        CONFORMITY = "conformity", "Соответствия"
        ORIGIN = "origin", "Происхождения"
        PHYTO = "phyto", "Карантинный"
        QUALITY = "quality", "Качества"

    number = models.CharField("номер", max_length=32, unique=True)
    kind = models.CharField("вид", max_length=16, choices=Kind.choices)
    good = models.ForeignKey(Good, verbose_name="товар",
                             on_delete=models.PROTECT,
                             related_name="certificates")
    issuer = models.CharField("орган выдачи", max_length=128)
    issued_date = models.DateField("дата выдачи")
    valid_until = models.DateField("действителен до")
    fgis_no = models.CharField("регистрация в ФГИС", max_length=32,
                               blank=True)
    qr_data = models.CharField("данные QR-кода", max_length=128, blank=True)

    class Meta:
        verbose_name = "сертификат"
        verbose_name_plural = "сертификаты"
        ordering = ["valid_until"]

    def __str__(self):
        return f"{self.kind}: {self.number}"

    @property
    def days_to_expiry(self):
        return (self.valid_until - timezone.now().date()).days

    @property
    def expires_soon(self):
        return 0 <= self.days_to_expiry <= 30


class DocRequirement(models.Model):
    """Комплект документов: требование и отметка о наличии."""

    class Status(models.TextChoices):
        MISSING = "missing", "Отсутствует"
        PROVIDED = "provided", "Предоставлен"
        CHECKED = "checked", "Проверен"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="doc_requirements")
    doc_type = models.ForeignKey(DocType, verbose_name="тип документа",
                                 on_delete=models.PROTECT,
                                 related_name="requirements")
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.MISSING)
    document = models.ForeignKey(
        Document, verbose_name="загруженный документ",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="used_in_requirements")
    note = models.CharField("примечание", max_length=191, blank=True)

    class Meta:
        verbose_name = "требование к комплекту"
        verbose_name_plural = "требования к комплекту"
        ordering = ["order", "doc_type"]
        constraints = [
            models.UniqueConstraint(fields=["order", "doc_type"],
                                    name="docrequirement_unique"),
        ]

    def __str__(self):
        return f"{self.order.number}: {self.doc_type.code}"


class ComplianceCheck(models.Model):
    """Результат самопроверки соответствия требованиям."""

    class Result(models.TextChoices):
        PASSED = "passed", "Пройдена"
        ISSUES = "issues", "Есть замечания"
        FAILED = "failed", "Не пройдена"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="compliance_checks")
    checked_at = models.DateTimeField("проверено", auto_now_add=True)
    result = models.CharField("результат", max_length=16,
                              choices=Result.choices)
    checker = models.ForeignKey(settings.AUTH_USER_MODEL,
                                verbose_name="проверяющий",
                                on_delete=models.SET_NULL, null=True,
                                related_name="compliance_checks")
    note = models.TextField("замечания", blank=True)

    class Meta:
        verbose_name = "проверка соответствия"
        verbose_name_plural = "проверки соответствия"
        ordering = ["-checked_at"]

    def __str__(self):
        return f"{self.order.number}: {self.result}"


class DeadlineReminder(models.Model):
    """Напоминание о сроке действия документа или сертификата."""

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        SENT = "sent", "Отправлено"
        ACKED = "acked", "Подтверждено"
        CANCELED = "canceled", "Отменено"

    target_kind = models.CharField("вид объекта", max_length=16)
    target_id = models.PositiveBigIntegerField("код объекта")
    due_date = models.DateField("напоминание о дате")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  verbose_name="получатель",
                                  on_delete=models.CASCADE,
                                  related_name="deadline_reminders")
    sent_at = models.DateTimeField("отправлено", null=True, blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.PENDING)

    class Meta:
        verbose_name = "напоминание о сроке"
        verbose_name_plural = "напоминания о сроках"
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.target_kind}#{self.target_id}: {self.due_date}"


# ======================================================================
# Класс «K»: двуязычная коммуникация
# ======================================================================

class Dialog(models.Model):
    """Двуязычный диалог, привязанный к бизнес-объекту."""

    class SubjectKind(models.TextChoices):
        RFQ = "rfq", "Запрос"
        QUOTE = "quote", "Предложение"
        ORDER = "order", "Заказ"
        SHIPMENT = "shipment", "Партия"
        INCIDENT = "incident", "Инцидент"

    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    subject_kind = models.CharField("тип объекта", max_length=16,
                                    choices=SubjectKind.choices)
    subject_id = models.PositiveBigIntegerField("код объекта")
    subject_label = models.CharField("обозначение объекта", max_length=128,
                                     blank=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name="участники",
        related_name="dialogs")
    status = models.CharField("статус", max_length=8,
                              choices=Status.choices, default=Status.OPEN)
    last_message_at = models.DateTimeField("последнее сообщение",
                                           null=True, blank=True)

    class Meta:
        verbose_name = "диалог"
        verbose_name_plural = "диалоги"
        ordering = ["-last_message_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["subject_kind", "subject_id"],
                name="dialog_subject_unique"),
        ]

    def __str__(self):
        return f"{label('Диалог')}: {self.subject_label or self.subject_id}"


class Message(models.Model):
    """Сообщение участника диалога."""

    class Language(models.TextChoices):
        RU = "ru", "Русский"
        ZH = "zh", "中文"

    dialog = models.ForeignKey(Dialog, verbose_name="диалог",
                               on_delete=models.CASCADE,
                               related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name="автор",
                               on_delete=models.PROTECT,
                               related_name="messages")
    body = models.TextField("текст")
    language = models.CharField("язык", max_length=2,
                                choices=Language.choices,
                                default=Language.RU)
    created_at = models.DateTimeField("отправлено", auto_now_add=True)

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"
        ordering = ["dialog", "created_at"]
        indexes = [models.Index(fields=["dialog", "created_at"])]

    def __str__(self):
        who = self.author.get_username()
        return f"{who}: {self.body[:40]}"


class Translation(models.Model):
    """Машинный перевод сообщения."""

    message = models.ForeignKey(Message, verbose_name="сообщение",
                                on_delete=models.CASCADE,
                                related_name="translations")
    source_language = models.CharField("исходный язык", max_length=2)
    target_language = models.CharField("язык перевода", max_length=2)
    text = models.TextField("перевод")
    engine = models.CharField("движок перевода", max_length=32,
                              default="manual")
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "перевод"
        verbose_name_plural = "переводы"
        ordering = ["message", "target_language"]
        constraints = [
            models.UniqueConstraint(
                fields=["message", "target_language"],
                name="translation_message_target_unique"),
        ]

    def __str__(self):
        return f"{label('Перевод')} #{self.message_id} → {self.target_language}"


class Attachment(models.Model):
    """Файл, прикреплённый к сообщению, документу или инциденту."""

    file = models.FileField("файл", upload_to="attach/%Y/%m")
    owner_kind = models.CharField("тип владельца", max_length=16)
    owner_id = models.PositiveBigIntegerField("код владельца")
    size_bytes = models.BigIntegerField("размер, байт", null=True, blank=True)
    mime_type = models.CharField("MIME-тип", max_length=96, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="загрузил",
        on_delete=models.SET_NULL, null=True, related_name="attachments")
    created_at = models.DateTimeField("загружено", auto_now_add=True)

    class Meta:
        verbose_name = "вложение"
        verbose_name_plural = "вложения"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.owner_kind}#{self.owner_id}"


# ======================================================================
# Класс «A»: задачи, уведомления, аналитика, расчёты
# ======================================================================

class Task(DocNumberMixin, TimeStampedModel):
    """Задача, порождённая событием предметной области."""

    number_prefix = "TSK"

    class Source(models.TextChoices):
        ORDER = "order", "Заказ"
        RFQ = "rfq", "Запрос"
        DOCUMENT = "document", "Документ"
        INCIDENT = "incident", "Инцидент"
        MANUAL = "manual", "Вручную"

    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        NORMAL = "normal", "Обычный"
        HIGH = "high", "Высокий"

    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Выполнена"
        CANCELED = "canceled", "Отменена"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    title = models.CharField("заголовок", max_length=191)
    source_kind = models.CharField("источник", max_length=16,
                                   choices=Source.choices,
                                   default=Source.MANUAL)
    source_id = models.PositiveBigIntegerField("код источника", null=True,
                                               blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 verbose_name="исполнитель",
                                 on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name="tasks")
    due_date = models.DateField("срок", null=True, blank=True)
    priority = models.CharField("приоритет", max_length=8,
                                choices=Priority.choices,
                                default=Priority.NORMAL)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices, default=Status.NEW)

    class Meta:
        verbose_name = "задача"
        verbose_name_plural = "задачи"
        ordering = ["status", "due_date"]
        indexes = [models.Index(fields=["assignee", "status"])]

    def __str__(self):
        return f"{self.number}: {self.title}"

    @property
    def is_overdue(self):
        return (self.status in (self.Status.NEW, self.Status.IN_PROGRESS)
                and self.due_date is not None
                and self.due_date < timezone.now().date())


class TaskReminder(models.Model):
    """Напоминание о задаче по выбранному каналу."""

    class Channel(models.TextChoices):
        IN_APP = "in_app", "В приложении"
        EMAIL = "email", "Электронная почта"
        PUSH = "push", "Push"

    task = models.ForeignKey(Task, verbose_name="задача",
                             on_delete=models.CASCADE,
                             related_name="reminders")
    channel = models.CharField("канал", max_length=8,
                               choices=Channel.choices,
                               default=Channel.IN_APP)
    send_at = models.DateTimeField("время отправки")
    is_sent = models.BooleanField("отправлено", default=False)

    class Meta:
        verbose_name = "напоминание задачи"
        verbose_name_plural = "напоминания задач"
        ordering = ["send_at"]

    def __str__(self):
        return f"{self.task.number} → {self.get_channel_display()}"


class NotificationSetting(models.Model):
    """Правило: по какому событию и в какой канал слать уведомление."""

    class Event(models.TextChoices):
        RFQ_ANSWERED = "rfq_answered", "Ответ на запрос"
        QUOTE_CHANGED = "quote_changed", "Изменение предложения"
        ORDER_CHANGED = "order_changed", "Изменение заказа"
        DOC_EXPIRING = "doc_expiring", "Истекает документ"
        INCIDENT_NEW = "incident_new", "Новый инцидент"
        TASK_DUE = "task_due", "Срок задачи"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "В приложении"
        EMAIL = "email", "Электронная почта"
        PUSH = "push", "Push"

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name="пользователь",
                             on_delete=models.CASCADE,
                             related_name="notification_settings")
    event = models.CharField("событие", max_length=32,
                             choices=Event.choices)
    channel = models.CharField("канал", max_length=8,
                               choices=Channel.choices,
                               default=Channel.IN_APP)
    is_enabled = models.BooleanField("включено", default=True)

    class Meta:
        verbose_name = "настройка уведомления"
        verbose_name_plural = "настройки уведомлений"
        ordering = ["user", "event"]
        constraints = [
            models.UniqueConstraint(fields=["user", "event", "channel"],
                                    name="notifsetting_unique"),
        ]

    def __str__(self):
        return (f"{self.user.get_username()}:"
                f" {self.event} → {self.channel}")


class Notification(models.Model):
    """Личное уведомление участника."""

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  verbose_name="получатель",
                                  on_delete=models.CASCADE,
                                  related_name="notifications")
    kind = models.CharField("тип", max_length=32)
    title = models.CharField("заголовок", max_length=191)
    body = models.TextField("текст", blank=True)
    link = models.CharField("ссылка перехода", max_length=191, blank=True)
    is_read = models.BooleanField("прочитано", default=False)
    created_at = models.DateTimeField("отправлено", auto_now_add=True)

    class Meta:
        verbose_name = "уведомление"
        verbose_name_plural = "уведомления"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self):
        return f"{self.recipient.get_username()}: {self.title}"


class Metric(models.Model):
    """Определение показателя аналитической панели."""

    class Period(models.TextChoices):
        DAY = "day", "Сутки"
        WEEK = "week", "Неделя"
        MONTH = "month", "Месяц"

    code = models.CharField("код", max_length=32, unique=True)
    name_ru = models.CharField("название (рус.)", max_length=96)
    name_zh = models.CharField("название (кит.)", max_length=96)
    formula = models.CharField("формула расчёта", max_length=191, blank=True)
    unit = models.CharField("единица", max_length=16, blank=True)
    period = models.CharField("период", max_length=8,
                              choices=Period.choices,
                              default=Period.MONTH)

    class Meta:
        verbose_name = "показатель"
        verbose_name_plural = "показатели"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name_ru}"


class MetricSnapshot(models.Model):
    """Значение показателя за период (для панелей и истории)."""

    metric = models.ForeignKey(Metric, verbose_name="показатель",
                               on_delete=models.CASCADE,
                               related_name="snapshots")
    period_key = models.CharField("период", max_length=16,
                                  help_text="Например: 2026-09")
    value = models.DecimalField("значение", max_digits=14,
                                decimal_places=2)
    calculated_at = models.DateField("рассчитано")

    class Meta:
        verbose_name = "снимок показателя"
        verbose_name_plural = "снимки показателей"
        ordering = ["-period_key"]
        constraints = [
            models.UniqueConstraint(fields=["metric", "period_key"],
                                    name="metricsnapshot_unique"),
        ]

    def __str__(self):
        return f"{self.metric.code} {self.period_key} = {self.value}"


class ComplianceRisk(models.Model):
    """Выявленный риск соответствия по заказу."""

    class Level(models.TextChoices):
        LOW = "low", "Низкий"
        MEDIUM = "medium", "Средний"
        HIGH = "high", "Высокий"
        CRITICAL = "critical", "Критический"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.CASCADE,
                              related_name="risks")
    kind = models.CharField("вид риска", max_length=64)
    probability = models.CharField("вероятность", max_length=8,
                                   choices=Level.choices,
                                   default=Level.LOW)
    impact = models.CharField("ущерб", max_length=8, choices=Level.choices,
                              default=Level.MEDIUM)
    level = models.CharField("уровень", max_length=8,
                             choices=Level.choices, default=Level.LOW)
    advice = models.TextField("рекомендация", blank=True)
    detected_at = models.DateField("выявлен", default=timezone.now)

    class Meta:
        verbose_name = "риск соответствия"
        verbose_name_plural = "риски соответствия"
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.order.number}: {self.kind}"


class Statement(DocNumberMixin, TimeStampedModel):
    """Счёт на оплату по заказу."""

    number_prefix = "STM"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        ISSUED = "issued", "Выставлен"
        PARTIALLY_PAID = "partial", "Частично оплачен"
        PAID = "paid", "Оплачен"
        DISPUTED = "disputed", "Оспаривается"

    number = models.CharField("номер", max_length=24, unique=True,
                              blank=True)
    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.PROTECT,
                              related_name="statements")
    currency = models.ForeignKey(Currency, verbose_name="валюта",
                                 on_delete=models.PROTECT,
                                 related_name="statements")
    amount = models.DecimalField("сумма", max_digits=14, decimal_places=2)
    due_date = models.DateField("срок оплаты", null=True, blank=True)
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices,
                              default=Status.DRAFT)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="подтвердил",
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="statements_confirmed")

    class Meta:
        verbose_name = "счёт"
        verbose_name_plural = "счета"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(check=Q(amount__gte=Decimal("0")),
                                   name="statement_amount_non_negative"),
        ]

    def __str__(self):
        return f"{self.number} ({self.order.number})"


class StatementLine(models.Model):
    """Строка расчётного документа."""

    class Source(models.TextChoices):
        ORDER = "order", "Заказ"
        TRANSPORT = "transport", "Перевозка"
        DUTY = "duty", "Таможня"
        OTHER = "other", "Прочее"

    statement = models.ForeignKey(Statement, verbose_name="счёт",
                                  on_delete=models.CASCADE,
                                  related_name="lines")
    description = models.CharField("назначение платежа", max_length=191)
    qty = models.DecimalField("количество", max_digits=12,
                              decimal_places=3, default=Decimal("1"))
    price = models.DecimalField("цена", max_digits=12, decimal_places=2)
    source = models.CharField("источник", max_length=16,
                              choices=Source.choices, default=Source.ORDER)

    class Meta:
        verbose_name = "строка счёта"
        verbose_name_plural = "строки счетов"
        ordering = ["statement", "pk"]
        constraints = [
            models.CheckConstraint(
                check=Q(qty__gt=Decimal("0"), price__gte=Decimal("0")),
                name="statementline_values_positive"),
        ]

    @property
    def amount(self):
        return (self.qty * self.price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.description}: {self.amount}"


class Reconciliation(models.Model):
    """Сверка расчётов с контрагентом за период."""

    class Status(models.TextChoices):
        NEW = "new", "Начата"
        IN_PROGRESS = "in_progress", "В работе"
        RESOLVED = "resolved", "Сверена"

    order = models.ForeignKey(Order, verbose_name="заказ",
                              on_delete=models.PROTECT,
                              related_name="reconciliations")
    partner = models.CharField("контрагент", max_length=128)
    period = models.CharField("период", max_length=16,
                              help_text="Например: 2026-09")
    our_amount = models.DecimalField("наша сумма", max_digits=14,
                                     decimal_places=2)
    partner_amount = models.DecimalField("сумма партнёра", max_digits=14,
                                         decimal_places=2)
    diff = models.DecimalField("разница", max_digits=14, decimal_places=2,
                               default=Decimal("0"))
    status = models.CharField("статус", max_length=16,
                              choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        verbose_name = "сверка расчётов"
        verbose_name_plural = "сверки расчётов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.partner} {self.period}"

    def save(self, *args, **kwargs):
        self.diff = self.our_amount - self.partner_amount
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Регистрация платежа по счёту (платежи вне платформы)."""

    statement = models.ForeignKey(Statement, verbose_name="счёт",
                                  on_delete=models.PROTECT,
                                  related_name="payments")
    paid_date = models.DateField("дата регистрации", default=timezone.now)
    amount = models.DecimalField("сумма", max_digits=14, decimal_places=2)
    channel_note = models.CharField("канал и реквизиты", max_length=191,
                                    blank=True)
    buyer_confirmed = models.BooleanField("подтвердил закупщик",
                                          default=False)
    supplier_confirmed = models.BooleanField("подтвердил поставщик",
                                             default=False)
    created_at = models.DateTimeField("создано", auto_now_add=True)

    class Meta:
        verbose_name = "регистрация платежа"
        verbose_name_plural = "регистрации платежей"
        ordering = ["-paid_date"]
        constraints = [
            models.CheckConstraint(check=Q(amount__gt=Decimal("0")),
                                   name="payment_amount_positive"),
        ]

    def __str__(self):
        return f"{self.statement.number}: {self.amount}"

    @property
    def is_confirmed(self):
        return self.buyer_confirmed and self.supplier_confirmed


# ======================================================================
# Класс «S»: системные сущности
# ======================================================================

class AuditLog(models.Model):
    """Запись журнала действий (администрирование)."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL,
                              verbose_name="субъект",
                              on_delete=models.SET_NULL, null=True,
                              related_name="audit_entries")
    action = models.CharField("действие", max_length=64)
    target_kind = models.CharField("тип объекта", max_length=32)
    target_id = models.CharField("код объекта", max_length=32)
    before = models.TextField("до изменения", blank=True)
    after = models.TextField("после изменения", blank=True)
    ip_address = models.GenericIPAddressField("IP-адрес", null=True,
                                              blank=True)
    created_at = models.DateTimeField("событие", auto_now_add=True)

    class Meta:
        verbose_name = "запись журнала"
        verbose_name_plural = "журнал действий"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_kind", "created_at"])]

    def __str__(self):
        who = self.actor.get_username() if self.actor else label("система")
        return f"{who}: {self.action} {self.target_kind}#{self.target_id}"


class SystemParam(models.Model):
    """Параметр системы, редактируемый администратором."""

    key = models.SlugField("ключ", max_length=64, unique=True)
    value = models.TextField("значение")
    note = models.CharField("назначение", max_length=191, blank=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        verbose_name = "параметр системы"
        verbose_name_plural = "параметры системы"
        ordering = ["key"]

    def __str__(self):
        return self.key


__all__ = [
    "TimeStampedModel", "Incoterm", "TransportMode",
    "Currency", "Country", "Uom", "GoodCategory", "Industry",
    "BorderCrossing", "TransportLane", "Tariff",
    "Profile", "Enterprise", "Membership", "Invitation", "Counterparty",
    "Good", "Packaging", "ProductImage",
    "Rfq", "RfqLine", "Quote", "QuoteLine", "QuoteVersion",
    "Order", "OrderLine", "OrderMilestone", "OrderChange",
    "Shipment", "Transport", "TrackPoint", "Incident",
    "DocType", "Document", "Certificate", "DocRequirement",
    "ComplianceCheck", "DeadlineReminder",
    "Dialog", "Message", "Translation", "Attachment",
    "Task", "TaskReminder", "NotificationSetting", "Notification",
    "Metric", "MetricSnapshot", "ComplianceRisk",
    "Statement", "StatementLine", "Reconciliation", "Payment",
    "AuditLog", "SystemParam",
]
