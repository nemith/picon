#! /usr/bin/env python3


from agent import APIClient

a = APIClient.APIClient('http://199.187.221.170:5000/api/')
a.register()
