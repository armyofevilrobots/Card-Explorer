#!/usr/bin/env python

"""
Card Explorer
Written by Colin Keigher
http://afreak.ca
All items in here are licensed under the LGPL (see LICENCE.TXT)

Release notes
====================================================================
0.4 (December 13, 2012)
- Checks against ISO/IEC 7812 upon initial scan.
- Improved the input mechanism so the data is sort of sanitised.
- Reading of financial cards works a bit better per ISO/IEC 7813.
- Added some items that will address rewards cards, but this has yet to be added to Main() function.

0.2 (December 6, 2012)
- Predictive input for a second track.
- Able to work with two types of financial cards. Some don't have more than two tracks.
- Moved service codes into the database.
- Added additional values to the IIN search in case items are missing.
- Rewrote the functions so it is a bit more organised.
- Made preparations for other types of card formats for a later version.

0.1 (December 5, 2012) 
- Initial release. Includes IIN searching.
"""

import calendar
import sqlite3 as lite

"""
This is really the belly of the beast which will handle the scanning and then the determination of 
what sort of card it might be.
"""

def Main():
	# For now you can only scan financial cards that start with %B--this will change.
	
	CardData = MainInput()

	# Time to sort out the data here. What sort of card is this?
	if CardData[0][:1] == chr(37): # If we start with a % in the start sentinal, let's work with the data this way.
		if CardData[0][1:2] == "B": # Let's do this if we think it's ISO compliant.
			if "^" in CardData[0]:
				if int(CardData[0][2:3]) in [3, 4, 5, 6]:
					print FCCardOutput(CardData[0][2:].split("^")) # Presuming it is a financial card here.
				else:
					print CardData[0][2:].split("^")
					print CardData[0][2:3]
			else:
				MainExitMsg("Not recognised yet!")
		else:
			MainExitMsg("Not recognised yet!")
	if CardData[:1] == ";": # Some cards use this as the sentinal.
		if int(CardData[1:2]) in [4, 5, 6]:
			if CardData.split("=")[1] == None:
				MainExitMsg("Not recognised yet!")
			else:
				# This format I have not run across except with RBC cards. Any else? It lacks a name.
				CardData = [ CardData.split("=")[0][1:], "No data", CardData.split("=")[1] ]
				print FCCardOutput(CardData)
		else:
			MainExitMsg("Not recognised yet!")

	print " "

def MainCardType(value):
	return MainDBQuery("SELECT * FROM CardType WHERE ID=" + str(value))[1]

def MainInput():
	print "Please swipe your card through the reader (hit enter to skip a track):"
	InputStr = str(raw_input(">> "))
	if InputStr[0:1] == chr(37): # Preparing for a two-track card scan.
		InputStr = [ InputStr, str(raw_input(">> ")) ]
	print " "
	return InputStr

def MainExitMsg(msg):
	print msg
	quit()

def MainDisplayOutput(mtype, string):
	print ""
	print "Card type: ", MainCardType(mtype)
	if mtype == 0:
		OtherCard(string)
	if mtype == 1:
		FCCardOutput(string)

"""
Below are items specifically written for financial cards. This would include bank cards, credit cards, 
and some forms of gift cards. The code below can be used for other types of cards too.
"""

# Generates a friendly card number in the format of XXXX XXXX XXXX XXXX and so forth.
# Will spit out a value if otherwise.
def FCFriendlyNumber(cnumber): 
	numlen = len(cnumber)
	if numlen == 16: # This is meant for most cards (Visa, MC, Bank)
		output = cnumber[0:4] + " " + cnumber[4:8] + " " + cnumber[8:12] + " " + cnumber[12:]
	elif numlen == 15: # American Express has this format.
		output = cnumber[0:4] + " " + cnumber[4:10] + " " + cnumber[10:]
	elif numlen == 9: # Probably safe to display it as XXX XXX XXX
		output = cnumber[0:3] + " " + cnumber[3:6] + " " + cnumber[6:]
	else: 
		output = cnumber
	return output

# Outputs a YYMM value from a card into a human-readable format.
def FCDateFormat(strdate): 
	output = calendar.month_name[int(strdate[2:])] + " " + strdate[0:2]
	if int(strdate[2:]) > 12:
		output = "Smarch? (fake value?)" # "Smarch" weather, while notoriously bad, does not exist!
	return output

def FCCardOutput(strcard):
	# There are some odd cards out there that may not be a financial card and therefore will not have a service code.
	if len(strcard[2][4:7]) < 3:
		FCServiceCode = "Odd format. Are you sure it is a financial card?"
	else:
		FCServiceCode = str(strcard[2][4:7]) + " (" + FCServiceDecode(strcard[2][4:7]) + ")"
	
	print "Card type:       ", ISOCardType(strcard[0][:1])
	print "Card number:     ", FCFriendlyNumber(strcard[0])
	print "Card holder:     ", strcard[1]
	print "Expiration date: ", FCDateFormat(strcard[2][0:4])
	print "Service code:    ", FCServiceCode
	print "Issuer:          ", FCINNSearch(strcard[0][:6])

# Returns a friendly value for the card's service codes.
def FCServiceDecode(code):
	if int(code) == 000:
		return "No information"
	else:
		return FCServiceDecodeReturn(1, int(code[0:1])) + ", " + \
		FCServiceDecodeReturn(2, int(code[1:2])) + ", " + \
		FCServiceDecodeReturn(3, int(code[2:3]))

# This will be a lot better once I move all of this into the SQLite DB
def FCServiceDecodeReturn(numtype, digit):
	return MainDBQuery("SELECT * FROM ServiceCode WHERE ID=" + str(numtype) + str(digit))[1]

# Makes a DB query using MainDBQuery() to pull an IIN.
# Starts off with a 6 digit search, then 4, then 2 all to provide an accurate result.
def FCINNSearch(string):
	# We'll attempt to get something a bit more specific using 6-digits
	try:
		output = MainDBQuery("SELECT * FROM IINs WHERE IIN LIKE " + str(string))[1]
	except:
		# Should that fail, we'll attempt 4-digits
		try:
			output = MainDBQuery("SELECT * FROM IINs WHERE IIN LIKE " + str(string[0:4]))[1]
		# We'll go generic or go broke! I'll add more as we go along.
		except:
			if int(string[0:2]) in [33, 34, 37]:
				output = "American Express"
				# Okay. So we know it's an AMEX, but what type?
				if int(string[0:2]) == 37 and int(string[4:6]) in [66, 24, 26, 28]:
					output = output + " (Gift card)"
			elif int(string[0:2]) == 35:
				output = "JCB Credit Card"
			elif int(string[0:2]) == 36:
				output = "Diners Club International"
			elif int(string[0:2]) >= 40 and int(string[0:2]) <= 49:
				output = "Visa"
			elif int(string[0:2]) >= 50 and int(string[0:2]) <= 55:
				output = "MasterCard"
			elif int(string[0:2]) in [56, 67]:
				output = "Maestro"
			elif int(string[0:2]) in [57, 58, 66]:
				output = "Possible bank card"
			elif int(string[0:2]) in [60, 63]:
				output = "Miscilaneous gift card or store credit card"
			else:
				output = "Unable to determine issuer"
	return output


"""
Miscilaneous cards. Some of these will make perfect sense and others will not and therefore we have to guess?
Some of this includes generic functions.
"""

def ISOCardType(value):
	return MainDBQuery("SELECT * FROM ISOCardTypes WHERE ID=" + str(value))[1]

# This is meant for working with rewards cards from stores and so forth.
def OtherCard(string):
	print "Card number: ", FCFriendlyNumber(filter(lambda x: x.isdigit(), string[0])[OtherIIN(0, string[0]):])
	print "IIN: ", OtherIIN(2, string[0])
	print "Issuer: ", OtherIIN(1, string[0]) # This will be worked on for a later version.

# This will search IINs for values and their types
def OtherIIN(status, iin):
	# Let's clear out the special characters left over so we can search.
	iin = filter(lambda x: x.isdigit(), iin)
	# Same as before, we'll try for six and if that fails, we'll go for four.
	try:
		output = MainDBQuery("SELECT * FROM IINs WHERE IIN LIKE " + str(iin)[:6])[1]
		valid = 6
	except:
		# And if six fails, try four and then if not, fail.
		try: 
			output = MainDBQuery("SELECT * FROM IINs WHERE IIN LIKE " + str(iin)[:4])[1]
			valid = 4
		except:
			output = "Unable to locate IIN"
			valid = 0
	if status == 2:
		if valid == 0:
			return "Not found"
		else:
			return str(iin)[:valid] 
	if status == 1: return output
	if status == 0: return valid

"""
Below is really meant for the meat and potatoes of the application.
It should start with the Main() function.
"""

# Needs error handling but it simplifies my queries
def MainDBQuery(query):
		con = lite.connect("iin.sqlite")
		cur = con.cursor()
		cur.execute(query)
		return cur.fetchone()
	
def MainErrorOut(message):
	print ""
	print message
	exit(1)

# Just because I want to maintain version numbers
AppVer = 0.4

print "Card Explorer", str(AppVer)
print "Created by Colin Keigher (http://afreak.ca)"
print " "

Main()