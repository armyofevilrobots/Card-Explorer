#!/usr/bin/env python

"""
Card Explorer
Written by Colin Keigher
http://afreak.ca
All items in here are licensed under the LGPL (see LICENCE.TXT)

Release notes
====================================================================
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
	print "Please swipe your card through the reader (hit enter to skip a track):"
	CardTrackInit = str(raw_input("Track 1: "))
	if CardTrackInit[0:1] == chr(37): # Preparing for a financial card scan.
		CardTrack1 = CardTrackInit.split("^")
		CardTrack2 = str(raw_input("Track 2: ")).split("=") # Allowing input to ensure that we don't spill over.
		if CardTrackInit[1:2] == "B":
			CardType = 1 # Value has been determined as a possible financial card.
		else:
			CardType = 0
	# Some cards start with "=", a lot of them being financial cards.
	elif CardTrackInit[0:1] == ";": 
		# The extra semi-colon is just for padding. Easier this way I guess?
		if CardTrackInit.find("=") != -1:
			CardTrack1 = [ ";" + CardTrackInit.split("=")[0], "Unknown (see card?)", CardTrackInit.split("=")[1] ]
			CardType = 1
		else:
			CardTrack1 = CardTrackInit	
			CardType = 0
	# No idea what the card is. Let's pass it on to other scripts.
	else:
		CardType = 0

	# If everything is good, we'll pass it on to the component that determines how to process and display the data.		
	MainDisplayOutput(CardType,CardTrack1)

def MainCardType(value):
	return MainDBQuery("SELECT * FROM CardType WHERE ID=" + str(value))[1]

def MainDisplayOutput(mtype, string):
	print ""
	print "Card type: ", MainCardType(mtype)
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
	else: 
		output = cnumber
	return output

# Outputs a YYMM value from a card into a human-readable format.
def FCDateFormat(strdate): 
	output = calendar.month_name[int(strdate[2:])] + " " + strdate[0:2]
	if int(strdate[0:2]) > 12:
		output = output + " (fake value?)" # "Smarch" weather, while notoriously bad, does not exist!
	return output

def FCCardOutput(strcard):
	# There are some odd cards out there that may not be a financial card and therefore will not have a service code.
	if len(strcard[2][4:7]) < 3:
		FCServiceCode = "Odd format. Are you sure it is a financial card?"
	else:
		FCServiceCode = strcard[2][4:7] + " (" + FCServiceDecode(strcard[2][4:7]) + ")"

	print "Card number: ", FCFriendlyNumber(strcard[0][2:])
	print "Card holder: ", strcard[1]
	print "Expiration date: ", FCDateFormat(strcard[2][:4])
	print "Service code: ", FCServiceCode
	print "Issuer: ", FCINNSearch(strcard[0][2:8])

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
		return MainDBQuery("SELECT * FROM IINs WHERE IIN LIKE " + str(string))[1]
	except:
		# Should that fail, we'll attempt 4-digits
		try:
			return MainDBQuery("SELECT * FROM IINs WHERE IIN LIKE " + str(string[0:4]))[1]
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
"""

# This is meant for working with rewards cards from stores and so forth.
def OtherCard(string):
	return "hello" # This will be worked on for a later version.

# This will search IINs for values and their types
def OtherIIN(qtype, iin):
	return "tbd"

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
AppVer = 0.2

print "Card Explorer", str(AppVer)
print "Created by Colin Keigher (http://afreak.ca)"
print " "

Main()