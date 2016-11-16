# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-14 17:21:47
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-11-14 17:25:59
import inspect

def __non_keyword_args(function):
    argspec = inspect.getargspec(function)
    pars = argspec[0][:len(argspec[3])]  # only non-keyword arguments
    return pars

