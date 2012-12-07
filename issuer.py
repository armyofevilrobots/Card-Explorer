#!/usr/bin/python

"""
Card Explorer
Written by Colin Keigher
http://afreak.ca
All items in here are licensed under the LGPL

Release notes
====================================================================
0.1 (December 5, 2012) - Initial release. Includes IIN searching.
"""

import calendar
import sqlite3 as lite

def initprompt():
	# For now you can only scan financial cards that start with %B--this will change.
	print "Please swipe your card through the reader (hit enter to skip a track):"
	CardTrack1 = str(raw_input("")).split("^")
	CardTrack2 = str(raw_input("")).split("=") # In a later version this won't come up if only one track is fed.

	# Making sure that the card belongs to a financial institution. This only works with B-types.
	if CardTrack1[0][1:2] != "B": errorout("Card cannot be decoded.")

	# This will become a function when I start to have it decode other types of cards.
	print " "
	print "Card Number: ", cardfriendly(CardTrack1[0][2:])
	print "Card Holder: ", CardTrack1[1]
	print "Expiration date: ", datefriendly(CardTrack1[2][:4])
	print "Service code: ", CardTrack1[2][4:7] + " (" + servicedecode(CardTrack1[2][4:7]) + ")"
	print "Issuer: ", iinsearch(CardTrack1[0][2:8])

def cardfriendly(cnumber): return cnumber[0:4] + " " + cnumber[4:8] + " " + cnumber[8:12] + " " + cnumber[12:]

def datefriendly(strdate): return calendar.month_name[int(strdate[2:])] + " " + strdate[0:2]

def servicedecode(code):
	if int(code) == 000:
		return "No information"
	else:
		return returnservicecode(1, int(code[0:1])) + ", " + \
		returnservicecode(2, int(code[1:2])) + ", " + \
		returnservicecode(3, int(code[2:3]))

# This will be a lot better once I move all of this into the SQLite DB
def returnservicecode(numtype, digit):
	if numtype == 1:
		if digit == 1: return "International"
		if digit == 2: return "International (requires EMV)"
		if digit == 5: return "National only"
		if digit == 6: return "National only (requires EMV)"
		if digit == 7: return "Institution only"
		if digit == 9: return "Test card"
	if numtype == 2:
		if digit == 0: return "Normal"
		if digit == 2: return "Must contact institution"
		if digit == 4: return "Must contact institution with exceptions"
	if numtype == 3:
		if digit == 0: return "Requires PIN"
		if digit == 1: return "No restrictions"
		if digit == 2: return "Goods and services only"
		if digit == 3: return "ATM only, Requires PIN"
		if digit == 4: return "Cash only"
		if digit == 5: return "Goods and services only, Requires PIN"
		if digit == 6: return "No restrictions, Use PIN if possible"
		if digit == 7: return "Goods and services only, Use PIN if possible"

# Needs error handling but it simplifies my queries
def dbquery(query):
		con = lite.connect("iin.sqlite")
		cur = con.cursor()
		cur.execute(query)
		return cur.fetchone()

def iinsearch(string):
	# We'll attempt to get something a bit more specific using 6-digits
	try:
		return dbquery("SELECT * FROM IINs WHERE IIN LIKE " + str(string))[1]
	except:
		# Should that fail, we'll attempt 4-digits
		try:
			return dbquery("SELECT * FROM IINs WHERE IIN LIKE " + str(string[0:4]))[1]
		# And we'll either return a generic card determination or a failure
		except:
			value = int(string[0:2])
			if value in [33, 34, 37]:
				output = "American Express"
			if value == 36:
				output = "Diners Club International"
			if value == 35:
				output = "JCB Credit Card"
			else:
				output = "Unable to determine issuer"
			return output
	
def errorout(message):
	print message
	exit(1)

print "Mag Stripe Explorer"
print "Created by Colin Keigher (http://afreak.ca)"
print " "

initprompt()