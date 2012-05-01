# -*- coding: utf-8 -*-
#   Mozo Menu Editor - Simple fd.o Compliant Menu Editor
#   Copyright (C) 2006  Travis Watkins
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Library General Public
#   License as published by the Free Software Foundation; either
#   version 2 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Library General Public License for more details.
#
#   You should have received a copy of the GNU Library General Public
#   License along with this library; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import xml.dom.minidom
import matemenu
import gi
from collections import Sequence
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf

DESKTOP_GROUP = GLib.KEY_FILE_DESKTOP_GROUP
KEY_FILE_FLAGS = GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS

def fillKeyFile(keyfile, items):
	for key, item in items.iteritems():
		if item is None:
			continue

		if isinstance(item, bool):
			keyfile.set_boolean(DESKTOP_GROUP, key, item)
		elif isinstance(item, Sequence):
			keyfile.set_string_list(DESKTOP_GROUP, key, item)
		elif isinstance(item, basestring):
			keyfile.set_string(DESKTOP_GROUP, key, item)

def getUniqueFileId(name, extension):
	append = 0
	while 1:
		if append == 0:
			filename = name + extension
		else:
			filename = name + '-' + str(append) + extension
		if extension == '.desktop':
			path = getUserItemPath()
			if not os.path.isfile(os.path.join(path, filename)) and not getItemPath(filename):
				break
		elif extension == '.directory':
			path = getUserDirectoryPath()
			if not os.path.isfile(os.path.join(path, filename)) and not getDirectoryPath(filename):
				break
		append += 1
	return filename

def getUniqueRedoFile(filepath):
	append = 0
	while 1:
		new_filepath = filepath + '.redo-' + str(append)
		if not os.path.isfile(new_filepath):
			break
		else:
			append += 1
	return new_filepath

def getUniqueUndoFile(filepath):
	filename, extension = os.path.split(filepath)[1].rsplit('.', 1)
	append = 0
	while 1:
		if extension == 'desktop':
			path = getUserItemPath()
		elif extension == 'directory':
			path = getUserDirectoryPath()
		elif extension == 'menu':
			path = getUserMenuPath()
		new_filepath = os.path.join(path, filename + '.' + extension + '.undo-' + str(append))
		if not os.path.isfile(new_filepath):
			break
		else:
			append += 1
	return new_filepath

def getItemPath(file_id):
	for path in GLib.get_system_data_dirs():
		file_path = os.path.join(path, 'applications', file_id)
	if os.path.isfile(file_path):
		return file_path
	return None

def getUserItemPath():
	item_dir = os.path.join(GLib.get_user_data_dir(), 'applications')
	if not os.path.isdir(item_dir):
		os.makedirs(item_dir)
	return item_dir

def getDirectoryPath(file_id):
	for path in GLib.get_system_data_dirs():
		file_path = os.path.join(path, 'desktop-directories', file_id)
		if os.path.isfile(file_path):
			return file_path
	return None

def getUserDirectoryPath():
	menu_dir = os.path.join(GLib.get_user_data_dir(), 'desktop-directories')
	if not os.path.isdir(menu_dir):
		os.makedirs(menu_dir)
	return menu_dir

def getUserMenuPath():
	menu_dir = os.path.join(GLib.get_user_config_dir(), 'menus')
	if not os.path.isdir(menu_dir):
		os.makedirs(menu_dir)
	return menu_dir

def getSystemMenuPath(file_id):
	for path in GLib.get_system_config_dirs():
		file_path = os.path.join(path, 'menus', file_id)
		if os.path.isfile(file_path):
			return file_path
	return None

def getUserMenuXml(tree):
	system_file = getSystemMenuPath(tree.get_menu_file())
	name = tree.root.get_menu_id()
	menu_xml = "<!DOCTYPE Menu PUBLIC '-//freedesktop//DTD Menu 1.0//EN' 'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>\n"
	menu_xml += "<Menu>\n  <Name>" + name + "</Name>\n  "
	menu_xml += "<MergeFile type=\"parent\">" + system_file +	"</MergeFile>\n</Menu>\n"
	return menu_xml

def getIcon(item):
	pixbuf, path = None, None
	if item is None:
		return None
	if isinstance(item, str):
		iconName = item
	else:
		iconName = item.get_icon()
	if iconName and not '/' in iconName and iconName[-3:] in ('png', 'svg', 'xpm'):
		iconName = iconName[:-4]
	icon_theme = Gtk.IconTheme.get_default()
	try:
		pixbuf = icon_theme.load_icon(iconName, 24, 0)
		path = icon_theme.lookup_icon(iconName, 24, 0).get_filename()
	except:
		if iconName and '/' in iconName:
			try:
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(iconName, 24, 24)
				path = iconName
			except:
				pass
		if pixbuf is None:
			if item.get_type() == matemenu.TYPE_DIRECTORY:
				iconName = 'mate-fs-directory'
			elif item.get_type() == matemenu.TYPE_ENTRY:
				iconName = 'application-default-icon'
			try:
				pixbuf = icon_theme.load_icon(iconName, 24, 0)
				path = icon_theme.lookup_icon(iconName, 24, 0).get_filename()
			except:
				return None
	if pixbuf is None:
		return None
	if pixbuf.get_width() != 24 or pixbuf.get_height() != 24:
		pixbuf = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.HYPER)
	return pixbuf

def removeWhitespaceNodes(node):
	remove_list = []
	for child in node.childNodes:
		if child.nodeType == xml.dom.minidom.Node.TEXT_NODE:
			child.data = child.data.strip()
			if not child.data.strip():
				remove_list.append(child)
		elif child.hasChildNodes():
			removeWhitespaceNodes(child)
	for node in remove_list:
		node.parentNode.removeChild(node)
