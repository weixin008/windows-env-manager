"""主题和样式配置"""

# 统一主题配置
UNIFIED_THEME = {
    'background': '#f0f2f5',      # 浅灰背景
    'foreground': '#2c3e50',      # 深蓝灰文字
    'button_bg': '#ffffff',       # 纯白按钮
    'button_fg': '#2c3e50',       # 深蓝灰按钮文字
    'entry_bg': '#ffffff',        # 纯白输入框
    'entry_fg': '#2c3e50',        # 深蓝灰输入文字
    'select_bg': '#1890ff',       # 蓝色选中背景
    'select_fg': '#ffffff',       # 白色选中文字
    'border': '#e4e9f0',          # 浅灰边框
    'category_bg': '#ffffff',     # 白色分类背景
    'category_fg': '#2c3e50',     # 深蓝灰分类文字
    'toolbar_bg': '#ffffff',      # 白色工具栏
    'statusbar_bg': '#f7f9fc',    # 浅灰状态栏
    'hover_bg': '#e6f7ff',        # 悬停背景色
    'active_bg': '#40a9ff',       # 激活背景色
    'error_fg': '#ff4d4f',        # 错误文字颜色
    'success_fg': '#52c41a',      # 成功文字颜色
    'warning_fg': '#faad14'       # 警告文字颜色
}

# 控件样式配置
WIDGET_STYLES = {
    'TFrame': {
        'background': UNIFIED_THEME['background'],
        'padding': 5
    },
    'TButton': {
        'background': UNIFIED_THEME['button_bg'],
        'foreground': UNIFIED_THEME['button_fg'],
        'padding': (10, 5),
        'relief': 'flat',
        'borderwidth': 1
    },
    'TLabel': {
        'background': UNIFIED_THEME['background'],
        'foreground': UNIFIED_THEME['foreground'],
        'padding': 5
    },
    'TEntry': {
        'fieldbackground': UNIFIED_THEME['entry_bg'],
        'foreground': UNIFIED_THEME['foreground'],
        'padding': 5,
        'borderwidth': 1
    },
    'Treeview': {
        'background': UNIFIED_THEME['background'],
        'foreground': UNIFIED_THEME['foreground'],
        'rowheight': 25,
        'padding': 2
    }
} 