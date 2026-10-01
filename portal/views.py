# -*- coding: utf-8 -*-
"""portal 应用的视图。

阶段 4（“应用页面模板”）。每个视图对应
``portal/pages.py`` 注册表中的一张页面，并经由提供器
``portal/datasets.py`` 从模型获取数据。

尚未编写提供器的页面以
原型形式渲染（用占位代替数据）——参见 ``datasets.coverage()``。
"""

from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .datasets import provider_for
from .i18n import DEFAULT_LANG, normalize, t, translate_blocks
from .pages import (PAGE_BY_NAME, PAGES, content_of, module_name, params_of,
                    purpose_of, title_of)


def set_language_view(request, code):
    """记住所选语言并返回原始页面。

        之所以需要单独的路由，是因为 Django 管理面板会把地址中的
        ``?lang=`` 参数当作未知的列表
        过滤器并返回多余的重定向。而这里地址保持
        干净，选择则保存在会话中。
    """
    lang = normalize(code)
    if lang:
        request.session["lang"] = lang
    target = request.GET.get("next") or "/"
    # 防范开放重定向：仅允许自身的路径
    if not target.startswith("/") or target.startswith("//"):
        target = "/"
    return redirect(target)


def _lang(request):
    """当前界面语言（参见 portal.middleware.LanguageMiddleware）。"""
    return getattr(request, "LANG", DEFAULT_LANG)


def _page_data(page, lang):
    """注册表条目，其名称和描述为当前语言版本。

        ``ru``/``zh``/``en`` 字段保留：模板会以提示形式显示第二种语言。
        历史键 ``purpose``/``content``（中文变体的
        同义词）会被当前语言的翻译覆盖——这样
        页面不再把俄语标题与中文正文混在一起。
    """
    data = dict(page)
    data["title"] = title_of(page, lang)
    data["purpose"] = purpose_of(page, lang)
    data["content"] = content_of(page, lang)
    data["params"] = params_of(page, lang)
    data["module_title"] = module_name(page["module"], lang)
    data["module_alt"] = module_name(
        page["module"], "ru" if lang == "zh" else "zh")
    return data


def _page(request, name, **extra):
    """根据注册表条目和数据提供器渲染页面。"""
    lang = _lang(request)
    page = PAGE_BY_NAME[name]
    provider = provider_for(name)
    context = {
        "page": _page_data(page, lang),
        "page_url": "/" + page["path"],
        "all_pages": PAGES,
        "prototype": provider is None,
        "blocks": [],
        "mode": None,
    }
    if provider is not None:
        data = provider(request, **extra) or {}
        context["blocks"] = translate_blocks(data.get("blocks", []), lang)
        context["mode"] = data.get("mode")
    context.update(extra)
    return render(request, "portal/page.html", context)



# ======================================================================
# M0. 通用页面
# ======================================================================

def index_view(request):
    """主页：平台概览和最新订单。"""
    lang = _lang(request)
    data = provider_for("index")(request)
    return render(request, "portal/index.html", {
        "page": _page_data(PAGE_BY_NAME["index"], lang),
        "prototype": False,
        "blocks": translate_blocks(data.get("blocks", []), lang),
        "mode": data.get("mode"),
    })


def about_view(request):
    """平台信息及其领域边界。"""
    return _page(request, "about")


def help_view(request):
    """帮助：各角色的操作说明和常见问题解答。"""
    return _page(request, "help")


#: 由 ``seed_demo`` 命令创建的演示账号
#: (所有账号的密码相同——参见登录表单上的提示)
DEMO_USERS = (
    ("admin", "login_role_admin"),
    ("ivanov", "login_role_buyer"),
    ("wang", "login_role_supplier"),
    ("petrov", "login_role_carrier"),
)


def _safe_next(request):
    """登录后的返回页面——仅允许自身的相对路径。

        校验会拦截形如 ``?next=https://…`` 的开放重定向，
        与 ``set_language_view`` 中的原则相同。
    """
    candidate = request.POST.get("next") or request.GET.get("next") or ""
    if candidate and url_has_allowed_host_and_scheme(
            candidate, allowed_hosts={request.get_host()},
            require_https=request.is_secure()):
        return candidate
    return ""


def login_view(request):
    """登录：校验凭据并开启会话。

        已登录的用户不会看到表单。登录成功后
        返回 ``?next=`` 指定的页面，或返回
        控制面板（``settings.LOGIN_REDIRECT_URL``）。
    """
    target = _safe_next(request) or reverse(settings.LOGIN_REDIRECT_URL)
    if request.user.is_authenticated:
        return redirect(target)

    username = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        user = authenticate(request, username=username,
                            password=request.POST.get("password", ""))
        if user is not None:
            # 登录会重建会话；所选语言要保留——否则，
            # 界面就会像退出时一样回到默认语言
            lang = _lang(request)
            auth_login(request, user)
            if lang != DEFAULT_LANG:
                request.session["lang"] = lang
            return redirect(target)

    lang = _lang(request)
    page = PAGE_BY_NAME["login"]
    return render(request, "portal/login.html", {
        "page": _page_data(page, lang),
        "page_url": "/" + page["path"],
        "username": username,
        "next": _safe_next(request),
        "form_error": request.method == "POST",
        "demo_users": [(name, t(role_key, lang))
                       for name, role_key in DEMO_USERS],
    })


def register_view(request):
    """注册新用户并关联到企业。"""
    return _page(request, "register")


def logout_view(request):
    """退出登录并结束会话。

        ``auth_logout()`` 会连同所选语言一起清空整个会话，
        因此该选择在退出时会被保存并恢复——否则
        界面会回到默认语言。
    """
    lang = _lang(request)
    auth_logout(request)
    if lang != DEFAULT_LANG:
        request.session["lang"] = lang
    return redirect("portal:index")


# ======================================================================
# M1. 企业与账号
# ======================================================================

def enterprise_profile_view(request):
    """企业资料：双语的注册信息和联系方式。"""
    return _page(request, "enterprise_profile")


def enterprise_verification_view(request):
    """主体认证：上传文件与审核状态。"""
    return _page(request, "enterprise_verification")


def enterprise_members_view(request):
    """员工与角色：组织构成和角色分配。"""
    return _page(request, "enterprise_members")


def enterprise_invitations_view(request):
    """邀请合作伙伴加入订单协作区。"""
    return _page(request, "enterprise_invitations")


# ======================================================================
# M2. 商品
# ======================================================================

def goods_list_view(request):
    """商品列表：支持筛选与卡片式展示。"""
    return _page(request, "goods_list")


def goods_detail_view(request, pk):
    """商品卡片：特性、合规、版本历史。"""
    return _page(request, "goods_detail", pk=pk)


def goods_form_view(request):
    """以分步表单创建和编辑商品。"""
    return _page(request, "goods_form")


# ======================================================================
# M3. 询价与报价
# ======================================================================

def rfq_list_view(request):
    """询价单列表：按回复状态分组。"""
    return _page(request, "rfq_list")


def rfq_create_view(request):
    """创建询价单：数量、目标价格、期限、交货地点。"""
    return _page(request, "rfq_create")


def rfq_detail_view(request, pk):
    """询价单卡片及关联的报价。"""
    return _page(request, "rfq_detail", pk=pk)


def quote_list_view(request):
    """报价列表：含版本与有效期。"""
    return _page(request, "quote_list")


def quote_detail_view(request, pk):
    """报价卡片：阶梯价格、版本、转至订单。"""
    return _page(request, "quote_detail", pk=pk)


# ======================================================================
# M4. 订单
# ======================================================================

def order_list_view(request):
    """订单列表：支持按状态筛选并突出显示异常事件。"""
    return _page(request, "order_list")


def order_detail_view(request, pk):
    """订单卡片：状态区、阶段刻度、操作区。"""
    return _page(request, "order_detail", pk=pk)


def order_milestones_view(request, pk):
    """订单执行阶段：登记与查看时间线。"""
    return _page(request, "order_milestones", pk=pk)


def order_changes_view(request, pk):
    """订单变更：需双方确认的变更单。"""
    return _page(request, "order_changes", pk=pk)


# ======================================================================
# M5. 物流与口岸
# ======================================================================

def shipment_list_view(request):
    """批次与运输：按批次跟踪状态。"""
    return _page(request, "shipment_list")


def shipment_detail_view(request, pk):
    """批次卡片：登记运输阶段与单证。"""
    return _page(request, "shipment_detail", pk=pk)


def exception_list_view(request):
    """在途异常事件列表及其处理进展。"""
    return _page(request, "exception_list")


def exception_create_view(request):
    """异常事件登记：照片、描述、时间与地点。"""
    return _page(request, "exception_create")


# ======================================================================
# M6. 单据与合规
# ======================================================================

def documents_list_view(request):
    """单证注册表：订单单证的齐全度与配送方式。"""
    return _page(request, "documents_list")


def documents_upload_view(request):
    """上传单证：支持版本控制与断点续传。"""
    return _page(request, "documents_upload")


def certificates_list_view(request):
    """证书有效期：提前 60/30/7 天发出提醒。"""
    return _page(request, "certificates_list")


def compliance_check_view(request):
    """合规自查：记录结果的检查清单。"""
    return _page(request, "compliance_check")


# ======================================================================
# M7. 双语沟通
# ======================================================================

def message_list_view(request):
    """对话列表：按业务对象分组。"""
    return _page(request, "message_list")


def message_detail_view(request, pk):
    """业务对象上下文中的对话，辅以翻译。"""
    return _page(request, "message_detail", pk=pk)


# ======================================================================
# M8. 任务与提醒
# ======================================================================

def task_board_view(request):
    """任务看板：“由我处理”“我的”“已逾期”。"""
    return _page(request, "task_board")


def task_detail_view(request, pk):
    """任务卡片：期限、处理历史、升级上报。"""
    return _page(request, "task_detail", pk=pk)


def notification_settings_view(request):
    """通知、渠道与“免打扰”时段的设置。"""
    return _page(request, "notification_settings")


# ======================================================================
# M9. 数据分析
# ======================================================================

def dashboard_view(request):
    """执行面板：汇总卡片与按状态的分布。"""
    lang = _lang(request)
    data = provider_for("dashboard")(request)
    return render(request, "portal/dashboard.html", {
        "page": _page_data(PAGE_BY_NAME["dashboard"], lang),
        "prototype": False,
        "blocks": translate_blocks(data.get("blocks", []), lang),
        "mode": data.get("mode"),
    })


def dashboard_logistics_view(request):
    """时效与成本：比较渠道、口岸与类别。"""
    return _page(request, "dashboard_logistics")


def dashboard_compliance_view(request):
    """合规风险：证书与单证缺失。"""
    return _page(request, "dashboard_compliance")


# ======================================================================
# M10. 结算与对账
# ======================================================================

def statement_list_view(request):
    """按订单和费用生成的账单列表。"""
    return _page(request, "statement_list")


def statement_detail_view(request, pk):
    """结算对账：逐项确认与差异。"""
    return _page(request, "statement_detail", pk=pk)


# ======================================================================
# M11. 系统管理
# ======================================================================

def audit_log_list_view(request):
    """审计日志：关键操作，只读。"""
    return _page(request, "audit_log_list")


def dictionary_list_view(request):
    """字典：口岸、渠道、术语、单证类型。"""
    return _page(request, "dictionary_list")
