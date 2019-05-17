#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: plain
@time:2019/5/13 下午8:29
"""
import sys

books = [['红楼梦', '曹雪芹', 50], ['三国义', '罗贯中', 55], ['西游记', '吴承恩', 60], ['水浒传', '施耐庵', 65]]
users = [['Tom', '123'], ['Mike', '321']]

flag = False


def login():
    print'请输入用户名：'
    username = input()
    print '请输入用户密码：'
    password = input()
    if [username, password] in users:
        print '登录成功！'
        flag = True
        fun()
    else:
        print '\n用户名不存在或密码错误！ 请重新登录！'


def register():
    username = input('请输入用户名：')
    password = input('请输入用户密码：')
    users.append([username, password])
    print '注册成功！'


def main():
    while True:
        print '\n\n    **********************'
        print '    *欢迎来到图书管理系统*'
        print '    **********************\n'
        print '*********************************'
        print '******   登录-------1  **********'
        print '******   注册-------2  **********'
        print '******   退出-------0  **********'
        print '*********************************\n'
        v = int(input('请输入对应的数字：'))
        if v == 2:
            register()
        elif v == 1:
            login()
        elif v == 0:
            sys.exit(0)


def fun():
    while True:
        print '\n***************************************'
        print '********  增加书籍--------1  **********'
        print '********  删除书籍--------2  **********'
        print '********  查找书籍--------3  **********'
        print '********  修改书籍--------4  **********'
        print '********  查看所有书籍----5  **********'
        print '********  返回主界面------6  **********'
        print '********  退出------------0  **********'
        print '***************************************\n'
        v = int(input('请输入对应的数字：\n'))
        if v == 1:
            bookname = input('请输入书名：')
            author = input('请输入作者：')
            price = int(input('请输入价格：'))
            books.append([bookname, author, price])
            print '\n添加书籍成功！'
        elif v == 2:
            bookname = input('请输入书名：')
            author = input('请输入作者：')

            price = int(input('请输入价格：'))
            if [bookname, author, price] in books:
                books.remove([bookname, author, price])
                print '\n删除书籍成功！'
            else:
                print '\n该书籍不存在！自动返回...'
        elif v == 3:
            bookname = input('请输入书名：')
            print()
            j = 0
            for i in books:
                if i[0] == bookname:
                    j = 1
                    print '书名：', i[0], '作者：', i[1], '价格：', i[2]
            if j == 0:
                print '该书籍不存在！自动返回...'
            print '\n查找结束!\n'
        elif v == 4:
            bookname = input('请输入书名：')
            author = input('请输入作者：')
            price = int(input('请输入价格：'))
            if [bookname, author, price] in books:
                books.remove([bookname, author, price])
                bookname = input('请输入修改后的书名：')
                author = input('请输入修改后的作者：')
                price = int(input('请输入修改后的价格：'))
                books.append([bookname, author, price])
                print '\n修改书籍成功！'
            else:
                print '\n该书籍不存在！自动返回...'
        elif v == 5:
            print '\n书名\t\t', '作者\t\t\t', '价格\n'
            for i in books:
                print i[0], '\t\t', i[1], '\t\t', i[2]
            print "=="
        elif v == 0:
            sys.exit(0)
        elif v == 6:
            main()


main()
