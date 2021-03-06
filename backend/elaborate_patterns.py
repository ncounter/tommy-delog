#!/usr/bin/python

import sys, os, re, json
from datetime import datetime
import utils

def main(source_path, pattern_file_name, pattern_url_known):
   if not utils.validate_param_list([source_path, pattern_file_name, pattern_url_known]):
      utils.print_eol(2)
      sys.stdout.writelines('elaborate_patterns.py cannot start, there is an error in received parameters')
      utils.print_eol(2)
      return

   sys.stdout.writelines('starting elaborate_patterns.py, please wait...')
   utils.print_eol(2)

   # evaluate files with the following name pattern only
   regex = re.compile(r'localhost_access_log.(\d{4,}-\d{2,}-\d{2,}).txt')
   source_file_list = sorted(filter(regex.search, os.listdir(source_path)))

   sys.stdout.writelines(['analizyng ', str(len(source_file_list)), ' files'])
   utils.print_eol(2)

   # log files list to screen
   sys.stdout.writelines('\n'.join(source_file_list))
   utils.print_separator()

   # if output file exists, remove it and recreate it
   if os.path.exists(pattern_file_name): os.remove(pattern_file_name)
   pattern_file = open(pattern_file_name , 'w+')

   # create a map of shaped object like {ip : {url, datetime}}
   sequence_map = {}

   for source_file_name in source_file_list:
      with open(source_path + source_file_name, 'r') as current_file:
         for line in tuple(current_file):
            # extract the values from the log line
            ip = utils.extract_ip_from(line)
            url = utils.extract_url_from(line)
            datetime = utils.extract_datetime_from(line)
            method = utils.extract_method_from(line)

            url_pattern = re.compile(pattern_url_known, re.MULTILINE|re.IGNORECASE)
            new_url_pattern_result = url_pattern.search(url)
            if new_url_pattern_result != None:
               obj = {}
               obj['url'] = url
               obj['datetime'] = datetime.strftime('%Y-%m-%d %H:%M:%S')
               obj['method'] = method
               if ip in sequence_map.keys():
                  existing_values = list()
                  existing_values.extend(sequence_map[ip])
                  existing_values.append(obj)
                  sequence_map[ip] = existing_values
               else:
                  sequence_map[ip] = [obj]

         current_file.close()

   # create a list of patterns in a shaped object like [{ from: "/from/url", to: "/to/url", count: pattern_count }]
   patterns = []
   # sequence of patterns has to be created by the same ip because it is a user workflow
   for ip in sequence_map.keys():
      sequence_list = list()
      sequence_list.extend(sequence_map[ip])
      for i in range(len(sequence_list) - 1):
         current_item, next_item = sequence_list[i], sequence_list[i + 1]

         # now we can ignore the user (ip) and start counting
         # occurrencies of the same from-to pattern

         # if added already, increase the counter
         if any(x for x in patterns
               if x['from']['url'] == current_item['url']
                  and x['to']['url'] == next_item['url']
                  and x['from']['method'] == current_item['method']
                  and x['to']['method'] == next_item['method']):
            existing_obj = next(x for x in patterns
                  if x['from']['url'] == current_item['url']
                     and x['to']['url'] == next_item['url']
                     and x['from']['method'] == current_item['method']
                     and x['to']['method'] == next_item['method'])

            existing_obj['count'] = existing_obj['count'] + 1
         # else, add it with counter = 1
         else:
            pattern_obj = {}
            pattern_obj['from'] = current_item
            pattern_obj['to'] = next_item
            pattern_obj['count'] = 1
            patterns.append(pattern_obj)

   # write statistics into JSON format
   utils.write_line(pattern_file, json.dumps(patterns))

   pattern_file.close()
   sys.stdout.writelines(['A new pattern file has been generated in `', os.path.abspath(pattern_file.name), '`'])
   utils.print_eol(2)
