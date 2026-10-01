# -*- coding: utf-8 -*-
"""面板主页上的指标卡片。

默认的主页回答的问题是「这里到底有什么」：
一份模型列表。像「逾期任务」或「未确认付款」这样的数字
在这种列表里完全看不见，只有打开相应的表并把它整个
通读一遍才能知道。卡片回答的是另一个问题：
「现在有什么需要立刻注意」。

标签通过 ``tr()``（字典 ``portal/i18n.py``）获取，和门户页面上
区块的标签一样：这些是新的界面字符串，而不是 ORM
元数据，因此 ``langcheck.admin_labels()`` 不检查它们——
由完整性总测试 ``portal/tests_i18n.py`` 负责。

所有统计都是带索引的普通 ``COUNT``；表不存在时
（还没有迁移的全新数据库）卡片显示「—」，而不是让页面崩溃。
"""

from django.db.models import Q
from django.utils import timezone

from . import models as m
from .i18n import active_lang, tr

#: 对证书和文档来说，多少天以内算「即将到期」。
EXPIRY_HORIZON_DAYS = 30


def _card(key, count, url, tone=""):
    """指标卡片：标签、数值和点击跳转。"""
    return {
        "key": key,
        "title": tr(key, active_lang()),
        "count": count,
        "url": url,
        "tone": tone,
    }


def _admin_url(model, **query):
    """面板中模型列表的地址，筛选条件由查询参数给定。"""
    from django.urls import NoReverseMatch, reverse

    meta = model._meta
    try:
        url = reverse("admin:%s_%s_changelist" % (meta.app_label,
                                                  meta.model_name))
    except NoReverseMatch:
        return None
    if not query:
        return url
    from urllib.parse import urlencode

    return "%s?%s" % (url, urlencode(query))


def _count(qs):
    """记录条数；表不存在时得到 None，而不是抛出异常。"""
    try:
        return qs.count()
    except Exception:                        # noqa: BLE001 ——数据库可能为空
        return None


def overdue_tasks():
    """截止期限已过且工作尚未完成的任务。"""
    today = timezone.now().date()
    return _count(m.Task.objects.filter(
        status__in=(m.Task.Status.NEW, m.Task.Status.IN_PROGRESS),
        due_date__lt=today))


def unconfirmed_payments():
    """未获双方确认的付款登记。

    确认是双向的：由采购方和供应方分别进行。等待
    第二个签认的付款，就是未结清的账目。
    """
    return _count(m.Payment.objects.filter(
        Q(buyer_confirmed=False) | Q(supplier_confirmed=False)))


def expiring_certificates():
    """在最近一个月内到期的证书。"""
    today = timezone.now().date()
    horizon = today + timezone.timedelta(days=EXPIRY_HORIZON_DAYS)
    return _count(m.Certificate.objects.filter(
        valid_until__gte=today, valid_until__lte=horizon))


def pending_invitations():
    """已发送且尚未被接受的邀请。"""
    return _count(m.Invitation.objects.filter(
        status=m.Invitation.Status.PENDING))


def critical_incidents():
    """高严重度且尚未关闭的异常事件。"""
    return _count(m.Incident.objects.filter(
        severity=m.Incident.Severity.HIGH,
        status__in=(m.Incident.Status.REGISTERED,
                    m.Incident.Status.IN_PROGRESS)))


def open_orders():
    """处理中的订单——未完成也未取消。"""
    return _count(m.Order.objects.exclude(status__in=(
        m.Order.Status.COMPLETED, m.Order.Status.CANCELED)))


#: 卡片按重要性排列。顺序是显式给出的：从「现在就需要
#: 处理」到「值得了解」，让视线自上而下沿着紧迫
#: 程度递减。
CARDS = (
    dict(key="Задачи просроченные", value=overdue_tasks,
         url=lambda: _admin_url(m.Task, status__in="new,in_progress"),
         tone="warn"),
    dict(key="Платежи без подтверждения", value=unconfirmed_payments,
         url=lambda: _admin_url(m.Payment, buyer_confirmed="0"),
         tone="danger"),
    dict(key="Сертификаты истекают", value=expiring_certificates,
         url=lambda: _admin_url(m.Certificate), tone="warn"),
    dict(key="Инциденты критические", value=critical_incidents,
         url=lambda: _admin_url(m.Incident, severity="high"), tone="danger"),
    dict(key="Приглашения ожидают", value=pending_invitations,
         url=lambda: _admin_url(m.Invitation, status="pending"), tone=""),
    dict(key="Заказы в работе", value=open_orders,
         url=lambda: _admin_url(m.Order), tone=""),
)


def overview():
    """主页的卡片。单个错误不应让整个页面崩溃。"""
    out = []
    for spec in CARDS:
        try:
            count = spec["value"]()
            url = spec["url"]()
        except Exception:                    # noqa: BLE001 ——面板必须保持可用
            count, url = None, None
        out.append(_card(spec["key"], count, url, spec["tone"]))
    return out
