# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-11-16 16:41:01

import pandas as pd

with open("timings.json", 'r') as fh:
    json_array_inside_text = fh.read()

json_array_text = "[" + json_array_inside_text[:-2] + "]"  # :-1 removes ,\n

df = pd.read_json(json_array_text)