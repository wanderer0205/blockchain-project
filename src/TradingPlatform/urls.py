"""TradingPlatform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.hello),
    path('logout/', views.logout),
    path('login/', views.get_login_html),
    path('login/sendLogin/', views.loginAccount),
    path('login/sendRegister/', views.register),
    path('basic/', views.get_basic_html),
    path('basic/sendBroke/', views.broke),
    path('choose/', views.get_choose_html),
    path('choose/getLevel/', views.getLevel),
    path('BillManage/', views.get_BillManage_html),
    path('BillManage/sendRevokeReceipt/', views.send_revoke),
    path('BillManage/sendAddReceipt/', views.send_addReceipt),
    path('BillManage/sendTransferReceipt/', views.send_transfer),
    path('BillManage/sendRepay/', views.send_repay),
    path('BillManage/sendFinance/', views.send_finance),
    path('BillManage/getAliveCommonCompanyName/', views.getAliveCommonCompanyName),
    path('BillManage/getAliveBankName/', views.getAliveBankName),
    path('BillManage/getAliveCompanyName/', views.getAliveCompanyName),
    path('BillManage/getCompanyName/', views.getCompanyName),
    path('BillManage/sendAgreeOrNot/', views.send_AgreeOrNot),
    path('BusinessManage/', views.get_BusinessManage_html),
    path('BusinessManage/sendChangeBusiness/', views.send_ChangeBusiness),
]
