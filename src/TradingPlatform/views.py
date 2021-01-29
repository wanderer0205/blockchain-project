from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

import os, json, sys, traceback
from myClient import myClient, tempClient
from client.bcosclient import BcosClient
from eth_account.account import Account
from client_config import client_config
from eth_utils.hexadecimal import encode_hex
from eth_utils import to_checksum_address
mclient = None

def hello(request):
    return redirect("/login/")

def get_login_html(request):
    global mclient
    if mclient is None:
        return render(request, "login.html")
    elif mclient.isOK==False:
        return render(request, "login.html")
    else:
        return redirect("/choose/")

def loginAccount(request):
    mess={'isSuss': 0, 'info': None}
    try:
        name = request.POST.get('user')
        password = request.POST.get('pass')
    except:
        mess['isSuss']=-2
        return JsonResponse(mess)
    global mclient
    mclient = myClient(name, password)
    if mclient is None:
        mess['isSuss']=-1
    elif mclient.isOK==False:
        mess['isSuss']=-1
    return JsonResponse(mess)

def register(request):
    mess={'isSuss': 0, 'info': None}
    try:
        name = request.POST.get('name')
        password = request.POST.get('pass')
        level = request.POST.get('level')
        credit = request.POST.get('credit')
    except:
        mess['isSuss']=-2
        mess['info']="获取参数失败！"
        return JsonResponse(mess)

    max_account_len = 240
    if len(name) > max_account_len:
        mess['isSuss']=-2
        mess['info']="企业名不得长于240个字符！"
        return JsonResponse(mess)
    print("starting : {} {} ".format(name, password))
    ac = Account.create(password)
    print("new address :\t", ac.address)
    print("new private_key :\t", encode_hex(ac.key))
    print("new public_key :\t", ac.publickey)

    tclient=None
    tclient=tempClient()
    if tclient.isOK!=True:
        mess['isSuss']=-1
        mess['info']="创建操作用户失败！"
        return JsonResponse(mess)
    
    res=tclient.register(name, level, credit, ac.address)
    if res==-1:
        mess['isSuss']=-1
        mess['info']="插入企业表时失败！"
        return JsonResponse(mess)
    elif res==-2:
        mess['isSuss']=-1
        mess['info']="同名企业仍在正常运营！"
        return JsonResponse(mess)

    kf = Account.encrypt(ac.privateKey, password)
    keyfile = "{}/{}.keystore".format(client_config.account_keyfile_path, name)
    print("save to file : [{}]".format(keyfile))
    with open(keyfile, "w") as dump_f:
        json.dump(kf, dump_f)
        dump_f.close()

    return JsonResponse(mess)

def logout(request):
    mess={'isSuss': 0}
    global mclient
    try:
        mclient=None
    except:
        mess['isSuss']=-1
    return JsonResponse(mess)

def get_choose_html(request):
    global mclient
    if mclient is None:
        return redirect("/login/")
    else:
        return render(request, 'choose.html')

def getLevel(request):
    global mclient
    mess={'level': None}
    mess['level']=mclient.account_level
    return JsonResponse(mess)

def get_basic_html(request):
    global mclient
    if mclient is None:
        return redirect("/login/")
    elif mclient.isOK==False:
        return redirect("/login/")
    mess = dict()
    mclient.renew_account_data()
    mess['name'] = mclient.account_name
    mess['address'] = mclient.account_address
    mess['status'] = mclient.account_status
    mess['level'] = mclient.account_level
    mess['credit'] = mclient.account_credit
    return render(request, 'basic.html', mess)

def broke(request):
    mess={'isSuss': 0, 'info': None}
    global mclient
    mess['isSuss']=mclient.broke()
    return JsonResponse(mess)
    
def getAliveCommonCompanyName(request):
    global mclient
    mess = {'name':list(), 'cname':mclient.account_name}
    result = mclient.getAllCompany()
    num = len(result)
    for i in range(num):
        if result[i]['status']==0 and result[i]['level']==2:
            mess['name'].append(result[i]['name'])
    return JsonResponse(mess)

def getAliveBankName(request):
    global mclient
    mess = {'name':list()}
    result = mclient.getAllCompany()
    num = len(result)
    for i in range(num):
        if result[i]['status']==0 and result[i]['level']==1:
            mess['name'].append(result[i]['name'])
    return JsonResponse(mess)

def getAliveCompanyName(request):
    global mclient
    mess = {'name':list(), 'cname':mclient.account_name}
    result = mclient.getAllCompany()
    num = len(result)
    for i in range(num):
        if result[i]['status']==0 and result[i]['level']==2:
            mess['name'].append(result[i]['name'])
    result = mclient.getAllCompany()
    num = len(result)
    for i in range(num):
        if result[i]['status']==0 and result[i]['level']==1:
            mess['name'].append(result[i]['name'])
    return JsonResponse(mess)

def getCompanyName(request):
    global mclient
    mess = {'name': mclient.account_name}
    return JsonResponse(mess)

def get_BillManage_html(request):
    global mclient
    if mclient is None:
        return redirect("/login/")
    elif mclient.isOK==False:
        return redirect("/login/")
    elif mclient.account_level==2:
        mess = {'FromReceiptsList': None, 'ToReceiptsList': None}
        mess['FromReceiptsList'] = mclient.getFromReceipt()
        mess['ToReceiptsList'] = mclient.getToReceipt()
        return render(request, "BillManage.html", mess)
    elif mclient.account_level==1:
        mess = {'ToReceiptsList': None}
        mess['ToReceiptsList'] = mclient.getAllReceipts()
        return render(request, "BillManage2.html", mess)
    else:
        return HttpResponse("Error!")

def send_addReceipt(request):
    mess={'isSuss': 0, 'info': None}
    global mclient
    try:
        ToBusiness = request.POST.get('name')
        bill = request.POST.get('sum')
        date = request.POST.get('time')
    except:
        mess['isSuss']=-2
        mess['info']="获取参数失败！"
        return JsonResponse(mess)
    mess['isSuss'] = mclient.purchase(ToBusiness, bill, date)
    if mess['isSuss']==-4:
        mess['info']="债务人(债权人)已破产/不存在！"
    elif mess['isSuss']==-3:
        mess['info']="需由债务人提交账单！"
    elif mess['isSuss']==-2:
        mess['info']="债务人信用不足！"
    elif mess['isSuss']==-1:
        mess['info']="账单提交失败！"
    return JsonResponse(mess)
    
def send_AgreeOrNot(request):
    mess={'isSuss': 0, 'info': None}
    try:
        Id = request.POST.get('id')
        choice = request.POST.get('choice')
    except:
        mess['isSuss']=-2
        mess['info']="获取参数失败！"
        return JsonResponse(mess)
    global mclient
    mess['isSuss']=mclient.verify(Id, choice)
    if mess['isSuss']==-1:
        mess['info']="交互失败！"
    elif mess['isSuss']==-2:
        mess['info']="更新信用失败！"
    return JsonResponse(mess)

def send_revoke(request):
    mess={'isSuss': 0, 'info': None}
    try:
        Id = request.POST.get('id')
    except:
        mess['isSuss']=-2
        mess['info']="获取参数失败！"
        return JsonResponse(mess)
    global mclient
    mess['isSuss']=mclient.revoke(Id)
    return JsonResponse(mess)

def send_repay(request):
    mess={'isSuss': 0, 'info': None}
    try:
        Id = request.POST.get('id')
        Sum = request.POST.get('sum')
    except:
        mess['isSuss']=-2
        mess['info']="获取参数失败！"
        return JsonResponse(mess)
    global mclient
    mess['isSuss']=mclient.repay(Id, Sum)
    return JsonResponse(mess)

def send_transfer(request):
    mess={'isSuss': 0, 'info': None}
    try:
        Id = request.POST.get('id')
        To = request.POST.get('to')
        Sum = request.POST.get('sum')
    except:
        mess['isSuss']=-2
        mess['info']="获取参数失败！"
        return JsonResponse(mess)
    global mclient
    mess['isSuss']=mclient.transfer(Id, To, Sum)
    return JsonResponse(mess)

def send_finance(request):
    mess={'isSuss': 0, 'info': None}
    try:
        Id = request.POST.get('id')
        To = request.POST.get('to')
        Sum = request.POST.get('sum')
    except:
        mess['isSuss']=-2
        mess['info']="获取参数失败！"
        return JsonResponse(mess)
    global mclient
    mess['isSuss']=mclient.finance(Id, To, Sum)
    return JsonResponse(mess)

def get_BusinessManage_html(request):
    global mclient
    if mclient is None:
        return redirect("/login/")
    elif mclient.isOK==False:
        return redirect("/login/")
    if mclient.account_level!=1:
        return HttpResponse("仅限登记注册的金融机构使用企业管理系统！")
    mess = {'CompanyList': list()}
    result = mclient.getAllCompany()
    num = len(result)
    for i in range(num):
        mess['CompanyList'].append([result[i]['name'],
                                    result[i]['address'],
                                    result[i]['level'],
                                    result[i]['status'],
                                    result[i]['credit']])
    return render(request, "BusinessManage.html", mess)

def send_ChangeBusiness(request):
    mess={'isSuss': 0, 'info': None}
    try:
        name = request.POST.get('name')
        address = request.POST.get('address')
        level = request.POST.get('level')
        status = request.POST.get('status')
        credit = request.POST.get('credit')
    except:
        mess['isSuss']=-2
        mess['info']="获取参数失败！"
        return JsonResponse(mess)
    global mclient
    mess['isSuss']=mclient.update_company(name, address, status, level, credit)
    return JsonResponse(mess)