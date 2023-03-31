#!/usr/bin/env python
# coding: utf-8

import re
import pandas as pd


def parser(output, samples=10, headers=None):
    # Define a regex pattern to match numerical values
    pattern = r'\d*\.\d+|\d+'
    result = []
    start_ind = 5
    
    for line in output.split('\n'):
        if not line:
            continue
        elif line.startswith('[ ID]'):
            if len(result) < samples:
                if headers is None:
                    start_ind = max(start_ind, line.rfind("]")) + 1
                    headers = [h.strip() for h in line[start_ind:].split("  ") if h.strip() != ""]

                result = []
                print(f"Headers of the output data: {', '.join(headers)}")
            else:
                break 
        elif headers and line.startswith('[  '):
            # Extract all numerical values from the string using the regex pattern
            num_matches = re.findall(pattern, line[start_ind:])
            if len(num_matches) < len(headers):
                continue
            else:
                # Convert the rest of the values to floats
                nums = [float(num) for num in num_matches]

                # Convert the first value to a float by subtracting two integers
                nums[1] = abs(nums[1] - nums[0])
                # Slice only significant values
                nums = nums[1:]
                row_values = nums[:len(headers)] if len(nums) > len(headers) else nums
                row_values[-1] = nums[-1]

                if len(result) < samples:
                    result.append(row_values)
        
        else:
            continue
            
    res_table = pd.DataFrame(result, columns=headers)
    return res_table

