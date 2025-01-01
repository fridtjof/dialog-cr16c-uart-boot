import configparser
from pprint import pprint
import json
import sys

FILENAME = None

if len(sys.argv) > 1:
	arg = sys.argv[1]
	if '.' in arg:
		FILENAME = arg.split('.')[0]
	else:
		FILENAME = arg
else:
	exit(-1)

def get_sfr(config):
	sfr = {}

	for k,v in config['Sfr'].items():
		parsed = v.split(',')
		parsed = [x.strip().replace('"', '') for x in parsed]

		def to_data(paramlist):
			data = {}
			data['zone_name'] = paramlist[0]
			data['addr'] = paramlist[1] #int(paramlist[1], 16)
			data['size'] = int(paramlist[2])
			data['base'] = int(paramlist[3].replace('base=', ''))
			if len(paramlist) > 4:
				# optional bit range
				data['bit_range'] = paramlist[4].replace('bitRange=', '')
			return data

		name = parsed[0]
		if '.' not in name: # main register def
			sfr[name] = to_data(parsed[1:])
		else: # subfield
			regname, fieldname = name.split('.')
			reg = sfr[regname]
			if 'fields' not in reg:
				reg['fields'] = {}
			reg['fields'][fieldname] = to_data(parsed[1:])
			sfr[regname] = reg

	#pprint(sfr)
	return sfr

# SfrReset section is ignored

def get_groups(config):
	groups = {}

	for k,v in config['SfrGroupInfo'].items():
		parsed = v.split(',')
		parsed = [x.strip().replace('"', '') for x in parsed]

		groupname = parsed[0]
		if groupname not in groups:
			groups[groupname] = []

		items = parsed[1:]
		groups[groupname].extend(items)

	#pprint(groups)
	return groups

key_counters = {}

def serialize_option_names(orig):
	if (orig[-1:].isdigit()): # already has a number
		return orig

	# append serialized numbers to every option name to avoid duplicates
	count = key_counters.get(orig)
	if count == None:
		key_counters[orig] = count = 0

	key_counters[orig] = key_counters[orig] + 1
	return orig + str(count)


print("FILENAME: " + str(FILENAME))

ddf_config = configparser.ConfigParser(strict=False)

key_counters = {}
ddf_config.optionxform = serialize_option_names
ddf_config.read(f'{FILENAME}.ddf', encoding='windows-1252')

def get_mmap(config):
	regions = {}

	for k,v in config['Memory'].items():
		parsed = v.split()
		#parsed = [x.strip().replace('"', '') for x in parsed]

		def to_data(paramlist):
			data = {}
			#data['AdrSpace'] = paramlist[0]
			data['start_addr'] = paramlist[1] #int(paramlist[1], 16)
			data['end_addr'] = paramlist[2] #int(paramlist[2], 16)
			data['permissions'] = paramlist[3]
			return data

		name = parsed[0]
		
		regions[name] = to_data(parsed[1:])

	#pprint(regions)
	return regions

mmap = get_mmap(ddf_config)

sfr_config = configparser.ConfigParser(strict=False)
key_counters = {}
sfr_config.optionxform = serialize_option_names

sfr_config.read(f'{FILENAME}.sfr', encoding='windows-1252')

sfr = get_sfr(sfr_config)
groups = get_groups(sfr_config)



outdata = {
	'sfr': sfr,
	'groups': groups,
	'mmap': mmap
}

with open(f"{FILENAME}.json", "w") as f:
	f.write(json.dumps(outdata))

