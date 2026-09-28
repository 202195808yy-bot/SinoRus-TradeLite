# 应用页面列表

《Python Web 应用开发》课程设计。

应用：「中俄跨境贸易轻量协同平台」——Web 客户端。

> 本文件由 `portal/pages.py` 自动生成（`python tools/gen_docs.py`），请勿手工编辑。

## 概览

| 指标 | 数值 |
|---|---|
| 页面总数 | 43 |
| 模块数 | 12 |
| 有独立 Django 路由的页面 | 42 |
| 由 `django.contrib.admin` 提供的页面 | 1 |

## 各模块的页面与地址

### M0. 公共页面

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 首页 | `/` | `index` | `index_view` | 公开 |
| 2 | 关于平台 | `/about/` | `about` | `about_view` | 公开 |
| 3 | 帮助与使用指南 | `/help/` | `help` | `help_view` | 公开 |
| 4 | 登录 | `/accounts/login/` | `login` | `login_view` | 公开 |
| 5 | 注册 | `/accounts/register/` | `register` | `register_view` | 公开 |
| 6 | 退出登录 | `/accounts/logout/` | `logout` | `logout_view` | 需登录 |

### M1. 企业与账号

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 企业双语档案 | `/enterprises/profile/` | `enterprise_profile` | `enterprise_profile_view` | 需登录 |
| 2 | 主体认证 | `/enterprises/verification/` | `enterprise_verification` | `enterprise_verification_view` | 需登录 |
| 3 | 成员与角色管理 | `/enterprises/members/` | `enterprise_members` | `enterprise_members_view` | 限角色 |
| 4 | 协作者邀请 | `/enterprises/invitations/` | `enterprise_invitations` | `enterprise_invitations_view` | 需登录 |

### M2. 商品管理

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 商品列表 | `/goods/` | `goods_list` | `goods_list_view` | 需登录 |
| 2 | 商品详情 | `/goods/<int:pk>/` | `goods_detail` | `goods_detail_view` | 需登录 |
| 3 | 新建/编辑商品 | `/goods/new/` | `goods_form` | `goods_form_view` | 需登录 |

### M3. 询价与报价

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 询价单列表 | `/rfqs/` | `rfq_list` | `rfq_list_view` | 需登录 |
| 2 | 发起询价 | `/rfqs/new/` | `rfq_create` | `rfq_create_view` | 需登录 |
| 3 | 询价单详情 | `/rfqs/<int:pk>/` | `rfq_detail` | `rfq_detail_view` | 需登录 |
| 4 | 报价单列表 | `/quotes/` | `quote_list` | `quote_list_view` | 需登录 |
| 5 | 报价单详情 | `/quotes/<int:pk>/` | `quote_detail` | `quote_detail_view` | 需登录 |

### M4. 订单管理

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 订单列表 | `/orders/` | `order_list` | `order_list_view` | 需登录 |
| 2 | 订单详情 | `/orders/<int:pk>/` | `order_detail` | `order_detail_view` | 需登录 |
| 3 | 履约里程碑 | `/orders/<int:pk>/milestones/` | `order_milestones` | `order_milestones_view` | 需登录 |
| 4 | 订单变更单 | `/orders/<int:pk>/changes/` | `order_changes` | `order_changes_view` | 需登录 |

### M5. 物流与口岸

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 运输批次列表 | `/shipments/` | `shipment_list` | `shipment_list_view` | 需登录 |
| 2 | 运输节点登记 | `/shipments/<int:pk>/` | `shipment_detail` | `shipment_detail_view` | 需登录 |
| 3 | 在途异常列表 | `/exceptions/` | `exception_list` | `exception_list_view` | 需登录 |
| 4 | 上报在途异常 | `/exceptions/new/` | `exception_create` | `exception_create_view` | 需登录 |

### M6. 单证与合规

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 单证清单 | `/documents/` | `documents_list` | `documents_list_view` | 需登录 |
| 2 | 单证上传 | `/documents/upload/` | `documents_upload` | `documents_upload_view` | 需登录 |
| 3 | 证书有效期管理 | `/certificates/` | `certificates_list` | `certificates_list_view` | 需登录 |
| 4 | 合规自查表 | `/compliance/self-check/` | `compliance_check` | `compliance_check_view` | 需登录 |

### M7. 双语沟通

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 会话列表 | `/messages/` | `message_list` | `message_list_view` | 需登录 |
| 2 | 会话详情 | `/messages/<int:pk>/` | `message_detail` | `message_detail_view` | 需登录 |

### M8. 任务与提醒

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 任务看板 | `/tasks/` | `task_board` | `task_board_view` | 需登录 |
| 2 | 任务详情 | `/tasks/<int:pk>/` | `task_detail` | `task_detail_view` | 需登录 |
| 3 | 提醒与免打扰设置 | `/notifications/settings/` | `notification_settings` | `notification_settings_view` | 需登录 |

### M9. 数据看板

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 履约看板 | `/dashboard/` | `dashboard` | `dashboard_view` | 需登录 |
| 2 | 时效与成本统计 | `/dashboard/logistics/` | `dashboard_logistics` | `dashboard_logistics_view` | 需登录 |
| 3 | 合规风险看板 | `/dashboard/compliance/` | `dashboard_compliance` | `dashboard_compliance_view` | 需登录 |

### M10. 结算与对账

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 账单列表 | `/statements/` | `statement_list` | `statement_list_view` | 需登录 |
| 2 | 对账详情 | `/statements/<int:pk>/` | `statement_detail` | `statement_detail_view` | 需登录 |

### M11. 系统管理

| 序号 | 页面 | 地址（URL） | 路由名 | 视图 | 访问权限 |
|---|---|---|---|---|---|
| 1 | 审计日志 | `/system/audit-logs/` | `audit_log_list` | `audit_log_list_view` | 限角色 |
| 2 | 基础字典维护 | `/system/dictionaries/` | `dictionary_list` | `dictionary_list_view` | 限角色 |
| 3 | Django 管理后台 | `/admin/` | `admin_index` | —（django.contrib.admin） | 限角色 |

## 页面描述

### M0. 公共页面

#### `/` — 首页

- **路由名：** `index`
- **视图：** `portal.views.index_view`
- **访问权限：** 公开
- **用途：** 向未登录访客与已登录用户展示平台定位、核心能力与当前待办概览。
- **主要内容：** 平台一句话定位、四类核心能力卡片、中俄贸易背景数据摘要、登录/注册入口；已登录时追加今日待办、异常订单、临期证书三张摘要卡。

#### `/about/` — 关于平台

- **路由名：** `about`
- **视图：** `portal.views.about_view`
- **访问权限：** 公开
- **用途：** 说明平台所处的产业链位置、四条业务边界与服务对象。
- **主要内容：** 平台定位（贸易协同层）、不做的四件事（资金业务、报关代理、合规结论判定、无关个人信息采集）、三类服务对象。

#### `/help/` — 帮助与使用指南

- **路由名：** `help`
- **视图：** `portal.views.help_view`
- **访问权限：** 公开
- **用途：** 提供按角色划分的操作指引与常见问题解答。
- **主要内容：** 按角色（中方贸易商、中方业务员、俄方合作方、货代操作员）分类的操作步骤、术语表、常见问题。

#### `/accounts/login/` — 登录

- **路由名：** `login`
- **视图：** `portal.views.login_view`
- **访问权限：** 公开
- **用途：** 校验用户身份并建立登录会话。
- **主要内容：** 账号与密码输入、记住登录状态、验证码登录切换、忘记密码入口；登录失败给出明确原因与剩余尝试次数。

#### `/accounts/register/` — 注册

- **路由名：** `register`
- **视图：** `portal.views.register_view`
- **访问权限：** 公开
- **用途：** 创建个人账号并绑定所属企业主体。
- **主要内容：** 手机号与邮箱注册（支持中国 +86 与俄罗斯 +7 区号）、密码强度校验、验证码倒计时、企业主体关联入口。

#### `/accounts/logout/` — 退出登录

- **路由名：** `logout`
- **视图：** `portal.views.logout_view`
- **访问权限：** 需登录
- **用途：** 结束当前会话并清理本地登录态。
- **主要内容：** 退出确认提示；退出后跳转至首页。

### M1. 企业与账号

#### `/enterprises/profile/` — 企业双语档案

- **路由名：** `enterprise_profile`
- **视图：** `portal.views.enterprise_profile_view`
- **访问权限：** 需登录
- **用途：** 维护企业主体的中俄双语档案，作为单证与合同自动填充的数据源。
- **主要内容：** 企业名称、统一社会信用代码 / ИНН（俄罗斯纳税人识别号）、注册地址、联系方式、银行信息；中俄双语字段并排填写，缺失项高亮提示补录。

#### `/enterprises/verification/` — 主体认证

- **路由名：** `enterprise_verification`
- **视图：** `portal.views.enterprise_verification_view`
- **访问权限：** 需登录
- **用途：** 提交并跟踪企业主体认证材料，控制未认证主体的功能范围。
- **主要内容：** 营业执照或俄方登记文件上传、字段识别结果确认、审核状态跟踪（待提交/审核中/已通过/已驳回）、驳回原因展示。

#### `/enterprises/members/` — 成员与角色管理

- **路由名：** `enterprise_members`
- **视图：** `portal.views.enterprise_members_view`
- **访问权限：** 限角色
- **用途：** 管理企业组织架构、成员账号与角色分配。
- **主要内容：** 成员列表（姓名、角色、状态、最近登录）、角色分配、账号停用与交接；仅业务负责人与管理员可见。

#### `/enterprises/invitations/` — 协作者邀请

- **路由名：** `enterprise_invitations`
- **视图：** `portal.views.enterprise_invitations_view`
- **访问权限：** 需登录
- **用途：** 邀请俄方合作方或货代操作员加入指定订单的协同范围。
- **主要内容：** 邀请对象类型选择、协同范围（按订单或按批次）、有效期设置、邀请链接与二维码、邀请状态跟踪。

### M2. 商品管理

#### `/goods/` — 商品列表

- **路由名：** `goods_list`
- **视图：** `portal.views.goods_list_view`
- **访问权限：** 需登录
- **用途：** 按品类、状态与关键词检索本企业商品卡片。
- **主要内容：** 卡片化列表（图片、中俄双语标题、规格摘要、合规属性标识）、常用筛选标签、排序、批量操作入口。

#### `/goods/<int:pk>/` — 商品详情

- **路由名：** `goods_detail`
- **视图：** `portal.views.goods_detail_view`
- **访问权限：** 需登录
- **路由参数：** pk — 商品标识
- **用途：** 展示商品完整信息、合规属性与历史版本。
- **主要内容：** 中俄双语标题与描述、规格参数、包装信息、图片集、HS 编码与合规属性、关联证书、版本历史与差异对比。

#### `/goods/new/` — 新建/编辑商品

- **路由名：** `goods_form`
- **视图：** `portal.views.goods_form_view`
- **访问权限：** 需登录
- **用途：** 录入或修改商品卡片，支持中俄双语字段。
- **主要内容：** 按基本信息、规格、包装、合规属性分四步填写，每步不超过 5 个字段；顶部进度指示；草稿自动保存。

### M3. 询价与报价

#### `/rfqs/` — 询价单列表

- **路由名：** `rfq_list`
- **视图：** `portal.views.rfq_list_view`
- **访问权限：** 需登录
- **用途：** 集中查看本企业发出与收到的询价单及其响应状态。
- **主要内容：** 按“我发起的 / 待我响应 / 已关闭”分组；列表项展示商品、数量、目标价区间、期望交期与剩余响应时间。

#### `/rfqs/new/` — 发起询价

- **路由名：** `rfq_create`
- **视图：** `portal.views.rfq_create_view`
- **访问权限：** 需登录
- **用途：** 由俄方合作方发起询价，明确数量、目标价与交期。
- **主要内容：** 商品选择、数量、目标价区间、期望交期、收货地、补充说明；一屏可填完，提交后即时通知中方。

#### `/rfqs/<int:pk>/` — 询价单详情

- **路由名：** `rfq_detail`
- **视图：** `portal.views.rfq_detail_view`
- **访问权限：** 需登录
- **路由参数：** pk — 询价单标识
- **用途：** 展示询价单全部条款与关联报价，支持直接响应。
- **主要内容：** 询价条款、发起方与时间、关联报价列表、状态流转记录、响应入口与会话入口。

#### `/quotes/` — 报价单列表

- **路由名：** `quote_list`
- **视图：** `portal.views.quote_list_view`
- **访问权限：** 需登录
- **用途：** 查看本企业发出与收到的报价单及其版本与有效期。
- **主要内容：** 列表项展示商品、单价与币种、贸易术语、有效期剩余天数、版本号；临期报价高亮提示。

#### `/quotes/<int:pk>/` — 报价单详情

- **路由名：** `quote_detail`
- **视图：** `portal.views.quote_detail_view`
- **访问权限：** 需登录
- **路由参数：** pk — 报价单标识
- **用途：** 展示报价全部条款、阶梯价与版本历史，支持转为订单。
- **主要内容：** 单价、币种、阶梯价、交期、贸易术语、有效期、备注；版本历史与差异对比；发出后不可直接修改，修改生成新版本。

### M4. 订单管理

#### `/orders/` — 订单列表

- **路由名：** `order_list`
- **视图：** `portal.views.order_list_view`
- **访问权限：** 需登录
- **用途：** 按状态、通道与时间检索订单，快速定位异常与超期订单。
- **主要内容：** 卡片化列表（订单号、对方企业、当前状态标签、关键时间、下一步动作）、状态筛选、异常订单置顶、导出入口。

#### `/orders/<int:pk>/` — 订单详情

- **路由名：** `order_detail`
- **视图：** `portal.views.order_detail_view`
- **访问权限：** 需登录
- **路由参数：** pk — 订单标识
- **用途：** 以“状态区 + 里程碑时间轴 + 操作区”三段式结构回答订单当前进度与下一步动作。
- **主要内容：** 顶部状态区（当前状态、下一步动作、责任方）；中部里程碑时间轴（节点、时间、操作人、凭证缩略图）；底部操作区（按角色与状态动态给出可执行动作）。

#### `/orders/<int:pk>/milestones/` — 履约里程碑

- **路由名：** `order_milestones`
- **视图：** `portal.views.order_milestones_view`
- **访问权限：** 需登录
- **路由参数：** pk — 订单标识
- **用途：** 按时间顺序登记与查看订单履约节点，形成可追溯的证据链。
- **主要内容：** 节点登记表单（节点类型、时间、操作人、说明、凭证上传）、时间轴全量展示、凭证查看与下载。

#### `/orders/<int:pk>/changes/` — 订单变更单

- **路由名：** `order_changes`
- **视图：** `portal.views.order_changes_view`
- **访问权限：** 需登录
- **路由参数：** pk — 订单标识
- **用途：** 以变更单方式记录数量、价格、交期与收货信息的调整，保留原值。
- **主要内容：** 变更项选择、变更前后值对照、变更原因、双方确认状态；未确认前原条款继续有效。

### M5. 物流与口岸

#### `/shipments/` — 运输批次列表

- **路由名：** `shipment_list`
- **视图：** `portal.views.shipment_list_view`
- **访问权限：** 需登录
- **用途：** 按批次跟踪货物运输状态与所属通道。
- **主要内容：** 批次列表（批次号、运输方式、通道、口岸、当前节点、预计到达时间）；支持按通道与口岸筛选。

#### `/shipments/<int:pk>/` — 运输节点登记

- **路由名：** `shipment_detail`
- **视图：** `portal.views.shipment_detail_view`
- **访问权限：** 需登录
- **路由参数：** pk — 运输批次标识
- **用途：** 登记提货至派送的各运输节点并上传凭证。
- **主要内容：** 运输方式与运单号、箱号与封号（支持扫码录入）、节点登记表单、时效偏差提示、凭证列表。

#### `/exceptions/` — 在途异常列表

- **路由名：** `exception_list`
- **视图：** `portal.views.exception_list_view`
- **访问权限：** 需登录
- **用途：** 集中查看在途异常及其处置进展。
- **主要内容：** 异常列表（异常分类、发生节点、上报人、上报时间、处置状态）；未处置异常置顶并高亮。

#### `/exceptions/new/` — 上报在途异常

- **路由名：** `exception_create`
- **视图：** `portal.views.exception_create_view`
- **访问权限：** 需登录
- **用途：** 在现场三步内完成异常上报，自动附带时间与位置。
- **主要内容：** 异常分类选择、情况说明、拍照上传（自动压缩并记录时间与位置）、关联订单与批次；离线可提交，恢复网络后自动同步。

### M6. 单证与合规

#### `/documents/` — 单证清单

- **路由名：** `documents_list`
- **视图：** `portal.views.documents_list_view`
- **访问权限：** 需登录
- **用途：** 按运输方式与商品品类展示订单所需单证清单及其齐备情况。
- **主要内容：** 清单项（单证类型、是否必需、是否已上传、有效版本、上传人、上传时间）；缺件项高亮并给出补件入口。

#### `/documents/upload/` — 单证上传

- **路由名：** `documents_upload`
- **视图：** `portal.views.documents_upload_view`
- **访问权限：** 需登录
- **用途：** 以拍照、相册或文件三种方式上传单证，并保留版本。
- **主要内容：** 上传方式选择、单证类型指定、文件类型与大小校验、上传进度与断点续传、版本标注（有效版本唯一）。

#### `/certificates/` — 证书有效期管理

- **路由名：** `certificates_list`
- **视图：** `portal.views.certificates_list_view`
- **访问权限：** 需登录
- **用途：** 登记证书信息并按 60/30/7 天分级提醒到期风险。
- **主要内容：** 证书列表（编号、签发方、生效日、到期日、剩余天数、关联商品与订单）；临期与过期按颜色分级；关联订单高亮。

#### `/compliance/self-check/` — 合规自查表

- **路由名：** `compliance_check`
- **视图：** `portal.views.compliance_check_view`
- **访问权限：** 需登录
- **用途：** 按清单逐项自查并留痕，作为发运前的检查依据。
- **主要内容：** 按运输方式生成的检查项清单、逐项勾选、不通过项填写原因、提交后生成留痕记录；平台只提示不判定结论。

### M7. 双语沟通

#### `/messages/` — 会话列表

- **路由名：** `message_list`
- **视图：** `portal.views.message_list_view`
- **访问权限：** 需登录
- **用途：** 按业务对象分组查看会话，避免沟通脱离业务上下文。
- **主要内容：** 会话列表（关联订单/批次/单证/对账单、对方企业、最后一条消息摘要、未读数）；未读会话置顶。

#### `/messages/<int:pk>/` — 会话详情

- **路由名：** `message_detail`
- **视图：** `portal.views.message_detail_view`
- **访问权限：** 需登录
- **路由参数：** pk — 会话标识
- **用途：** 在业务对象上下文中进行中俄双语沟通并留存记录。
- **主要内容：** 消息流、结构化消息模板选择、翻译辅助（标注“机器辅助翻译”并要求发送方确认）、术语库提示、文件与图片消息、按业务对象导出沟通记录。

### M8. 任务与提醒

#### `/tasks/` — 任务看板

- **路由名：** `task_board`
- **视图：** `portal.views.task_board_view`
- **访问权限：** 需登录
- **用途：** 按“待我处理 / 我发起的 / 已超时”分组呈现任务并支持筛选。
- **主要内容：** 三组看板列、任务卡片（标题、关联业务对象、责任人、剩余时限）、超时项置顶并高亮、筛选与批量操作。

#### `/tasks/<int:pk>/` — 任务详情

- **路由名：** `task_detail`
- **视图：** `portal.views.task_detail_view`
- **访问权限：** 需登录
- **路由参数：** pk — 任务标识
- **用途：** 展示任务详情、处理记录与升级链路。
- **主要内容：** 任务描述、关联业务对象、责任人、响应时限、处理记录、确认接收与转派、超时升级记录。

#### `/notifications/settings/` — 提醒与免打扰设置

- **路由名：** `notification_settings`
- **视图：** `portal.views.notification_settings_view`
- **访问权限：** 需登录
- **用途：** 配置各类事件的推送渠道、优先级与免打扰时段。
- **主要内容：** 事件类型与推送开关、推送渠道（应用内/短信/邮件）、免打扰时段（按各自本地时间生效）、语言与时区切换入口。

### M9. 数据看板

#### `/dashboard/` — 履约看板

- **路由名：** `dashboard`
- **视图：** `portal.views.dashboard_view`
- **访问权限：** 需登录
- **用途：** 以摘要卡与紧凑图表呈现履约整体状况。
- **主要内容：** 在途订单数量、状态分布、平均履约周期、超期订单清单；今日待办、异常订单、临期证书三张摘要卡，卡内数字即入口。

#### `/dashboard/logistics/` — 时效与成本统计

- **路由名：** `dashboard_logistics`
- **视图：** `portal.views.dashboard_logistics_view`
- **访问权限：** 需登录
- **用途：** 按通道、口岸与品类统计平均时效与费用构成。
- **主要内容：** 通道时效对比、口岸平均通关时长、费用构成（运费、报关费、仓储费、换装费）；支持按时间区间筛选与导出。

#### `/dashboard/compliance/` — 合规风险看板

- **路由名：** `dashboard_compliance`
- **视图：** `portal.views.dashboard_compliance_view`
- **访问权限：** 需登录
- **用途：** 汇总临期与过期证书、缺件订单与待完成自查项。
- **主要内容：** 风险清单按严重度排序（过期证书、临期证书、缺件订单、未完成自查）、一键跳转至处理页、导出风险报告。

### M10. 结算与对账

#### `/statements/` — 账单列表

- **路由名：** `statement_list`
- **视图：** `portal.views.statement_list_view`
- **访问权限：** 需登录
- **用途：** 依据订单与费用归集生成账单并跟踪确认状态。
- **主要内容：** 账单列表（关联订单、货值、运费、报关费、仓储费、合计、确认状态）；支持按时间区间与对方企业筛选。

#### `/statements/<int:pk>/` — 对账详情

- **路由名：** `statement_detail`
- **视图：** `portal.views.statement_detail_view`
- **访问权限：** 需登录
- **路由参数：** pk — 账单标识
- **用途：** 逐项确认账单条目，标记差异并记录争议过程。
- **主要内容：** 明细逐项确认、差异标记与原因填写、付款节点状态登记（已申请/已汇出/已到账，双方分别确认）、争议留痕与导出。

### M11. 系统管理

#### `/system/audit-logs/` — 审计日志

- **路由名：** `audit_log_list`
- **视图：** `portal.views.audit_log_list_view`
- **访问权限：** 限角色
- **用途：** 查询登录、权限变更、状态迁移与数据导出等关键操作记录。
- **主要内容：** 日志列表（操作人、时间、对象、操作类型、前后值）、按对象与时间检索、导出；日志只可查询不可删除。

#### `/system/dictionaries/` — 基础字典维护

- **路由名：** `dictionary_list`
- **视图：** `portal.views.dictionary_list_view`
- **访问权限：** 限角色
- **用途：** 维护口岸、通道、贸易术语、单证类型与异常原因分类等基础字典。
- **主要内容：** 字典分类树、词条增删改、启用与停用、双语词条维护；变更写入审计日志。

#### `/admin/` — Django 管理后台

- **路由名：** `admin_index`
- **视图：** `django.contrib.admin`
- **访问权限：** 限角色
- **用途：** 由 Django 框架自带的管理后台提供数据维护能力。
- **主要内容：** 模型注册、数据增删改查、用户与权限管理；由 django.contrib.admin 提供，不另行开发。
