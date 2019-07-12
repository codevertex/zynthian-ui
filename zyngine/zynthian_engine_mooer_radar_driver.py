# -*- coding: utf-8 -*-
#******************************************************************************
# ZYNTHIAN PROJECT: Zynthian Engine (zynthian_engine_mooer radar driver)
# 
# zynthian_engine implementation for controlling Mooer Radar via its USB
# 
# Copyright (C) 2019 Spencer Lovell <>
#
#******************************************************************************
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
# 
#******************************************************************************

import importlib
import re
import logging
import pexpect

from . import zynthian_engine

#------------------------------------------------------------------------------
# setBfree Engine Class
#------------------------------------------------------------------------------

class zynthian_engine_mooer_radar_driver(zynthian_engine):


	# ---------------------------------------------------------------------------
	# Banks
	# ---------------------------------------------------------------------------


	bank_list = [
		['Mooer Radar Bank 0', 0, 'Mooer Radar Bank 0', '_', [False, False, 59]]
	]


	# ---------------------------------------------------------------------------
	# Controllers & Screens
	# ---------------------------------------------------------------------------

	# MIDI Controllers
	_ctrls = [
		['volume',7,96,127]
	]

	# Controller Screens
	_ctrl_screens = [
		['main',['volume']]
	]

	# ---------------------------------------------------------------------------
	# Mooer Radar related
	# ---------------------------------------------------------------------------

	MOOER_RADAR_VENDOR_ID = 0x0483
	MOOER_RADAR_PRODUCT_ID = 0x5703

	PREDEFINED_RADAR_MSGS = [
		"0BAA550500E700000001CAA1",
		"0BAA550500E700000002FAC2",
		"0BAA550500E700000003EAE3",
		"0BAA550500E7000000049A04",
		"0BAA550500E7000000058A25",
		"0BAA550500E700000006BA46",
		"0BAA550500E700000007AA67",
		"0BAA550500E7000000085B88",
		"0BAA550500E7000000094BA9",
		"0BAA550500E70000000A7BCA",
		"0BAA550500E70000000B6BEB",
		"0BAA550500E70000000C1B0C",
		"0BAA550500E70000000D0B2D",
		"0BAA550500E70000000E3B4E",
		"0BAA550500E70000000F2B6F",
		"0BAA550500E700000010C8B1",
		"0BAA550500E700000011D890",
		"0BAA550500E700000012E8F3",
		"0BAA550500E700000013F8D2",
		"0BAA550500E7000000148835",
		"0BAA550500E7000000159814",
		"0BAA550500E700000016A877",
		"0BAA550500E700000017B856",
		"0BAA550500E70000001849B9",
		"0BAA550500E7000000195998",
		"0BAA550500E70000001A69FB",
		"0BAA550500E70000001B79DA",
		"0BAA550500E70000001C093D",
		"0BAA550500E70000001D191C",
		"0BAA550500E70000001E297F",
		"0BAA550500E70000001F395E",
		"0BAA550500E700000020FEE2",
		"0BAA550500E700000021EEC3",
		"0BAA550500E700000022DEA0",
		"0BAA550500E700000023CE81",
		"0BAA550500E700000024BE66"
	]

	#----------------------------------------------------------------------------
	# Initialization
	#----------------------------------------------------------------------------


	def __init__(self, zyngui=None):
		super().__init__(zyngui)
		self.name = "MooerRadarDriver"
		self.nickname = "RA"
		self.jackname = "mooerradardriver"

		self.usb_module = None
		self.usb_device = None

		self.options['midi_chan']=False

		self.base_dir = self.data_dir + "/mooerradardriver"

		self.bank_config = None

		#Process command ...
		# preset_fpath = self.base_dir + "/pgm/all.pgm"
		# config_fpath = self.base_dir + "/cfg/zynthian.cfg"
		# if self.config_remote_display():
		# 	self.command = "/usr/local/bin/setBfree -p \"{}\" -c \"{}\"".format(preset_fpath, config_fpath)
		# else:
		# 	self.command = "/usr/local/bin/setBfree -p \"{}\" -c \"{}\"".format(preset_fpath, config_fpath)

		self.command_prompt = "\nAll systems go."

		# Start engine
		logging.debug("STARTING MOOER RADAR DRIVER!!")
		self.start()
		#self.zyngui.zynautoconnect()

		self.reset()


	# def generate_config_file(self, midi_chans):
	# 	# Nothing to do
	# 	nothingToDo = True

	# ---------------------------------------------------------------------------
	# Custom Start/Stop
	# ---------------------------------------------------------------------------

	def start(self):
		if self.usb_module is None:
			logging.info("Starting Engine " + self.name)
			try:
				#self.start_loading()
				self.usb_module = importlib.import_module("usb")

				if self.usb_module is not None:
					return "All is cool"
				else:
					raise Exception("USB module not found!")

			except Exception as err:
				logging.error("Can't start engine {} => {}".format(self.name, err))

			#self.stop_loading()

	def stop(self):
		if self.usb_module is not None:
			#self.start_loading()
			try:
				logging.info("Stopping Engine " + self.name)
				del self.usb_module

			except Exception as err:
				logging.error("Can't stop engine {} => {}".format(self.name, err))

			#self.stop_loading()

	# ---------------------------------------------------------------------------
	# Mooer Radar Specific
	# ---------------------------------------------------------------------------

	def set_radar_preset(self, preset_number):
		logging.info("Preset change requested")

		if self.usb_module is not None:
			try:
				logging.info("Finding Mooer Radar over USB...")

				# Find the Mooer Radar USB device
				self.usb_device = self.usb_module.core.find(
					idVendor=self.MOOER_RADAR_VENDOR_ID, idProduct=self.MOOER_RADAR_PRODUCT_ID)

				# Did we find the device?
				if self.usb_device is not None:
					logging.info("Device Found!")

					# Claim the device and its interface
					if self.usb_device.is_kernel_driver_active(0):
						logging.info("Need to detach kernel driver, doing so now...")
						self.usb_device.detach_kernel_driver(0)
						logging.info("Done.")

					logging.info("Attempting to claim the USB interface...")
					self.usb_module.util.claim_interface(self.usb_device, 0)
					logging.info("Done.")

					# Send the preset change request
					logging.info("Sending preset change {} request over USB...".format(preset_number))
					message_to_use = self.PREDEFINED_RADAR_MSGS[int(preset_number) - 1]
					self.usb_device.write(2, message_to_use.decode("hex"))
					logging.info("Done.")
				else:
					logging.info("Device Not Found!")

			except Exception as err:
				logging.error("Failed to communicate with Mooer Radar: {}".format(err))

			try:
				# Release the device and interface
				logging.info("Releasing the interface...")
				self.usb_module.util.release_interface(self.usb_device, 0)
				logging.info("Done.")
				self.usb_device = None
			except Exception as err:
				logging.error("Failed to release USB device!")

	# ---------------------------------------------------------------------------
	# Layer Management
	# ---------------------------------------------------------------------------


	# ---------------------------------------------------------------------------
	# MIDI Channel Management
	# ---------------------------------------------------------------------------


	#----------------------------------------------------------------------------
	# Bank Managament
	#----------------------------------------------------------------------------


	def get_bank_list(self, layer):
		return self.bank_list

	def set_bank(self, layer, bank):
		self.set_radar_preset(bank)
		return True

	# 	# if not self.bank_config:
	# 	# 	self.bank_config = bank
	# 	# 	self.layers[0].load_bank_list()
	# 	# 	self.layers[0].reset_bank()
	# 	# 	return False
	#
	# 	if not self.proc:
	# 		midi_chans = [self.layers[0].get_midi_chan(), 15, 15]
	# 		free_chans = self.zyngui.screens['layer'].get_free_midi_chans()
	#
	# 		logging.info("Primary bank in channel {}".format(midi_chans[0]))
	# 		self.layers[0].bank_name = "Primary"
	# 		self.layers[0].load_bank_list()
	# 		self.layers[0].set_bank(0)
	#
	# 		# Start engine
	# 		logging.debug("STARTING MOOER RADAR DRIVER!!")
	# 		self.generate_config_file(midi_chans)
	# 		self.start()
	# 		self.zyngui.zynautoconnect()
	#
	# 		# midi_prog = self.bank_config[4][2]
	# 		# if midi_prog and isinstance(midi_prog, int):
	# 		# 	logging.debug("Loading bank configuration program: {}".format(midi_prog))
	# 		# 	self.zyngui.zynmidi.set_midi_prg(midi_chans[0], midi_prog)
	#
	# 		#self.zyngui.screens['layer'].fill_list()
	#
	# 		return True

	#----------------------------------------------------------------------------
	# Preset Managament
	#----------------------------------------------------------------------------


	def get_preset_list(self, bank):
		logging.debug("Preset List for Bank {}".format(bank[0]))
		pgm_list = [(0, [0, 0, "?"], "Mooer Radar Bank 0", "")]
		return pgm_list

	def set_preset(self, layer, preset, preload=False):
		if super().set_preset(layer,preset):
			self.update_controller_values(layer, preset)
			return True
		else:
			return False


	def cmp_presets(self, preset1, preset2):
		try:
			if preset1[0]==preset2[0]:
				return True
			else:
				return False
		except:
			return False


	#----------------------------------------------------------------------------
	# Controller Managament
	#----------------------------------------------------------------------------

	def update_controller_values(self, layer, preset):
	 	# Nothing to do
	 	nothingToDo = True

	# def midi_zctrl_change(self, zctrl, val):
	# 	try:
	# 		if val!=zctrl.get_value():
	# 			zctrl.set_value(val)
	# 			#logging.debug("MIDI CC {} -> '{}' = {}".format(zctrl.midi_cc, zctrl.name, val))
	#
	# 			#Refresh GUI controller in screen when needed ...
	# 			if self.zyngui.active_screen=='control' and self.zyngui.screens['control'].mode=='control':
	# 				self.zyngui.screens['control'].set_controller_value(zctrl)
	#
	# 	except Exception as e:
	# 		logging.debug(e)


	#----------------------------------------------------------------------------
	# Specific functionality
	#----------------------------------------------------------------------------


	# def get_chan_name(self, chan):
	# 	try:
	# 		return self.chan_names[chan]
	# 	except:
	# 		return None


	# def get_bank_dir(self, layer):
	# 	bank_dir=self.base_dir+"/pgm-banks"
	# 	chan_name=self.get_chan_name(layer.get_midi_chan())
	# 	if chan_name:
	# 		bank_dir=bank_dir+'/'+chan_name
	# 	return bank_dir


	# def load_program_list(self,fpath):
	# 	pgm_list = None
	# 	pgm_list.append((0, [0, 0, "?"], "Default", ""))
	# 	return pgm_list
	#
	# 	self.start_loading()
	# 	pgm_list=None
	# 	try:
	# 		with open(fpath) as f:
	# 			pgm_list=[]
	# 			lines = f.readlines()
	# 			ptrn1=re.compile("^([\d]+)[\s]*\{[\s]*name\=\"([^\"]+)\"")
	# 			ptrn2=re.compile("[\s]*[\{\}\,]+[\s]*")
	# 			i=0
	# 			for line in lines:
	# 				#Test with first pattern
	# 				m=ptrn1.match(line)
	# 				if not m: continue
	#
	# 				#Get line parts...
	# 				fragments=ptrn2.split(line)
	#
	# 				params={}
	# 				try:
	# 					#Get program MIDI number
	# 					prg=int(fragments[0])-1
	# 					if prg>=0:
	# 						#Get params from line parts ...
	# 						for frg in fragments[1:]:
	# 							parts=frg.split('=')
	# 							try:
	# 								params[parts[0].lower()]=parts[1].strip("\"\'")
	# 							except:
	# 								pass
	#
	# 						#Extract program name
	# 						title=params['name']
	# 						del params['name']
	#
	# 						#Add program to list
	# 						pgm_list.append((i,[0,0,prg],title,params))
	# 						i=i+1
	# 				except:
	# 					#print("Ignored line: %s" % line)
	# 					pass
	#
	# 	except Exception as err:
	# 		pgm_list=None
	# 		logging.error("Getting program info from %s => %s" % (fpath,err))
	#
	# 	self.stop_loading()
	# 	return pgm_list


	# ---------------------------------------------------------------------------
	# Extended Config
	# ---------------------------------------------------------------------------


	# def get_extended_config(self):
	# 	# Nothing to do
	# 	nothingToDo = True
	#
	#
	# def set_extended_config(self, xconfig):
	# 	# Nothing to do
	# 	nothingToDo = True


	# ---------------------------------------------------------------------------
	# Layer "Path" String
	# ---------------------------------------------------------------------------


	# def get_path(self, layer):
	# 	path = self.nickname
	# 	return path


#******************************************************************************
