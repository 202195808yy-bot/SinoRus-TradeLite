# -*- coding: utf-8 -*-
"""企业与账号 的视图（M0、M1）。

视图是薄壳：取注册表条目 ``core/pages.py``，
再调用数据提供器 ``accounts/datasets.py`` 组装上下文，
最后渲染 ``templates/portal/page.html``。通用逻辑在
``core/views.py``（``_page()`` / ``_page_data()`` / ``_lang()``）。
"""

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from core.views import _page, _page_data, _lang
from core.i18n import DEFAULT_LANG, t
from core.pages import PAGE_BY_NAME


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
    return redirect("core:index")


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
