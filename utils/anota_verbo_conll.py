#!/usr/bin/python
# -*- encoding: utf-8 -*-

PATH_OUTPUT = '/home/rafael/PycharmProjects/RBAMR/src/bin/resources/output/output.conll'
#PATH_OUTPUT = os.path.dirname(os.path.realpath(__file__)) + \
    #'/../src/bin/resource/output/output.conll'
PATH_PROPS = '/home/rafael/PycharmProjects/RBAMR/src/bin/resources/corpus/test/inputConst_Props.conll'
#PATH_PROPS = os.path.dirname(os.path.realpath(__file__)) + \
#    '/../src/bin/resource/corpus/test/inputConst_Props.conll'
#test_file_fp = open(PATH_PROPS, 'r')
#output_file_fp = open(PATH_OUTPUT, 'r')


def anota_verbo_conll():
	test_file_fp = open(PATH_PROPS, 'r')
	output_file_fp = open(PATH_OUTPUT, 'r')
	test_file_lines = test_file_fp.readlines()
	output_file_lines = output_file_fp.readlines()

	test_file_fp.close()
	output_file_fp.close()

	# Remove anotações de verbos
	for i in range(len(output_file_lines)):
	    if "(V*)" in output_file_lines[i]:
		substring_error = output_file_lines[i][output_file_lines[i].index('(V*'):]

		substring_error = substring_error[:substring_error.index(")") + 1]
		output_file_lines[i] = output_file_lines[i].replace(substring_error, "*           ")


	# Anota corretamente os verbos
	auxiliary_indexes = [(i, test_file_lines[i]) for i in range(len(test_file_lines)) if "(V*)" in test_file_lines[i]]
	for i in auxiliary_indexes:
	    splited_line_test = i[1].split("*")
	    target_verb_index = [j for j in range(len(splited_line_test)) if 'V' in splited_line_test[j]]

	    splited_line_output = output_file_lines[i[0]].split("*")[:-1]

	    for index in target_verb_index:
		if index == 0:
		    string = splited_line_test[index][:splited_line_test[index].index("V")]+splited_line_test[index][splited_line_test[index].index("V"):]+"*)"
		else:
		    string = "            (" + splited_line_test[index][splited_line_test[index].index("V"):]+"*)"

	    splited_line_output[index] = string
	    output_file_lines[i[0]] = "            *".join(splited_line_output)+'\n'


	new_output_file_fp = open(PATH_OUTPUT, 'w')
	for line in output_file_lines:
	    new_output_file_fp.write(line)
	new_output_file_fp.close()



def anota_auxiliares_conll():
	test_file_fp = open(PATH_PROPS, 'r')
	output_file_fp = open(PATH_OUTPUT, 'r')
	test_file_lines = test_file_fp.readlines()
	output_file_lines = output_file_fp.readlines()

	test_file_fp.close()
	output_file_fp.close()

	# Remove anotações de verbos
	for i in range(len(output_file_lines)):
	    if "(AM*)" in output_file_lines[i]:
		substring_error = output_file_lines[i][output_file_lines[i].index('(AM'):]

		substring_error = substring_error[:substring_error.index(")") + 1]
		output_file_lines[i] = output_file_lines[i].replace(substring_error, "*           ")


	# Anota corretamente os verbos
	auxiliary_indexes = [(i, test_file_lines[i]) for i in range(len(test_file_lines)) if "(AM" in test_file_lines[i]]
	for i in auxiliary_indexes:
	    splited_line_test = i[1].split("*")
	    target_verb_index = [j for j in range(len(splited_line_test)) if 'AM' in splited_line_test[j]]

	    splited_line_output = output_file_lines[i[0]].split("*")[:-1]

	    for index in target_verb_index:
		if index == 0:
		    string = splited_line_test[index][:splited_line_test[index].index("AM")]+splited_line_test[index][splited_line_test[index].index("AM"):]+"*)"
		else:
		    string = "            (" + splited_line_test[index][splited_line_test[index].index("AM"):]+"*)"

	    splited_line_output[index] = string
	    output_file_lines[i[0]] = "            *".join(splited_line_output)+'\n'


	new_output_file_fp = open(PATH_OUTPUT, 'w')
	for line in output_file_lines:
	    new_output_file_fp.write(line)
	new_output_file_fp.close()
