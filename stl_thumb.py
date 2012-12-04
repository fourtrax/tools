#!/usr/bin/env python
#  STL Thumbnail Generator
#  Copyright (C) 2012 Gerrit Wyen <gerrit@ionscale.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.



import os
import Image
import sys
import struct
import getopt

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *



inputfile = ""
outputfile = ""


def saveBufferAsPNG(filename):
	"""
	Save current gl buffer as png file 
	"""

	x,y,width,height = glGetDoublev(GL_VIEWPORT)
	width,height = int(width),int(height)

	glPixelStorei(GL_PACK_ALIGNMENT, 1)

	data = glReadPixels(x, y, width, height, GL_RGB, GL_UNSIGNED_BYTE)

	image = Image.fromstring( "RGB", (width, height), data )
	image = image.transpose( Image.FLIP_TOP_BOTTOM)

	image.save( filename, "PNG")





def parse_stl(name):
	""" 
	parse STL file 
	"""

	stlfile = open(name)

	maxPos = [0,0,0]
	minPos = [float("inf"),float("inf"),float("inf")]
	inFacet=False
	inLoop=False
	i = -1
	triangles = []

	try:

		if stlfile.read(5) == "solid":

			# Parse ASCII STL

			while True:
				line = stlfile.readline()
				if not line:
					break
				words = line.split()
				if len(words) < 1: continue

				if words[0] == "facet":
					inFacet = True

					i=i+1
					triangles.insert(i, [])
					x = float(words[2])
					y = float(words[3])
					z = float(words[4])
					triangles[i].append((x,y,z)) # normal vector
				elif words[0] == "outer":
					inLoop = True
		
	
				elif words[0] == "endfacet":
					inFacet = False
				elif words[0] == "endloop":
					inLoop = False


				elif words[0] == "vertex":
					x = float(words[1])
					y = float(words[2])
					z = float(words[3])

					if x > maxPos[0]: maxPos[0] = x
					if y > maxPos[1]: maxPos[1] = y
					if z > maxPos[2]: maxPos[2] = z

					if x < minPos[0]: minPos[0] = x
					if y < minPos[1]: minPos[1] = y
					if z < minPos[2]: minPos[2] = z

					triangles[i].append((x,y,z))
		else:

			# Parse binary STL

			stlfile.seek(80,0)
			numTriangles = struct.unpack('i', stlfile.read(4))[0]

			for i in range(numTriangles):
				triangles.insert(i, [])

				for v in range(4): # normal vector + 3x vertices
					x = struct.unpack('f', stlfile.read(4))[0]
					y = struct.unpack('f', stlfile.read(4))[0]
					z = struct.unpack('f', stlfile.read(4))[0]

					if x > maxPos[0]: maxPos[0] = x
					if y > maxPos[1]: maxPos[1] = y
					if z > maxPos[2]: maxPos[2] = z

					if x < minPos[0]: minPos[0] = x
					if y < minPos[1]: minPos[1] = y
					if z < minPos[2]: minPos[2] = z

					triangles[i].append((x,y,z))

				attributes = struct.unpack("h" ,stlfile.read(2))[0]

	except:
		print "Unable to parse STL file\n";
		print "Error:", sys.exc_info()[0]
		sys.exit(-1)


	return (triangles, maxPos, minPos)



def gl_init(width, height):
	"""
	Initialize OpenGL.
        """


	glutInit()
	glutInitWindowSize(width, height)
	glutCreateWindow("STL PREVIEW")
	glutHideWindow() # not very nice
	# TODO: make this work without a window, only rendering in offscreen buffer 

	glutInitDisplayMode(GLUT_DOUBLE |  GLUT_RGBA | GLUT_DEPTH)
	
	# Set callback for drawing
	glutDisplayFunc(display)


	glViewport( 0, 0, width, height )
	viewport = glGetIntegerv( GL_VIEWPORT )

	# Setup of perspective
	glMatrixMode( GL_PROJECTION )
	glLoadIdentity( )
	gluPerspective( 60.0, float( viewport[ 2 ] ) / float( viewport[ 3 ] ), 0.1, 1000.0 )
	glMatrixMode( GL_MODELVIEW )
	glLoadIdentity( )

	# Enable depth test
	glEnable(GL_DEPTH_TEST)
	# Accept closest fragment
	glDepthFunc(GL_LESS)

	#glShadeModel( GL_SMOOTH )
	glHint( GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST )





def display():
	"""
	callback for drawing opengl scene
	"""

	# Read stl file
	(triangles, maxPos, minPos) = parse_stl(inputfile)



	# Clear scene
	glClearColor( 0.9, 0.9, 0.9, 1.0 )
	glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
	glLoadIdentity( )


	
	# Set point of view (TODO: improve this)
	gluLookAt( maxPos[0]*1.4, maxPos[1]*1.4, maxPos[2]*2.0, 0, 0, 0, 0, 0, 1 )
	


	# Setup lighting

	light_ambient = [1.0, 1.0, 1.0, 1.0]
	light_diffuse = [1.0, 1.0, 1.0, 1.0]

	light_position = [maxPos[0]*2, maxPos[1]*2, maxPos[2]*1.7]

	glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
	glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
	glLightfv(GL_LIGHT0, GL_POSITION, light_position)


	glEnable(GL_LIGHTING)
	glEnable(GL_LIGHT0)


	# Setup material properties
	mat_specular = ( 1.0, 1.0, 1.0, 1.0 );
	mat_shininess = ( 50.0 );


	glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
	glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)

	glColorMaterial (GL_FRONT_AND_BACK, GL_DIFFUSE)
	glEnable (GL_COLOR_MATERIAL)


	# Draw triangle mesh of stl model

	glColor3f( 0.2, 0.4, 1 )

	for triangle in triangles:	
		glBegin(  GL_TRIANGLES )
		glNormal3d(triangle[0][0],triangle[0][1],triangle[0][2])
		glVertex3f(triangle[1][0],triangle[1][1],triangle[1][2])
		glVertex3f(triangle[2][0],triangle[2][1],triangle[2][2])
		glVertex3f(triangle[3][0],triangle[3][1],triangle[3][2])
		glEnd( )


	# Draw floor

	glColor3f( 0.9, 0.9, 0.9 )

	glBegin( GL_TRIANGLES )
	glNormal3d(0,0,1)
	glVertex3f(2000,-2000,minPos[2]-2)
	glVertex3f(-2000,2000,minPos[2]-2)
	glVertex3f(-2000,-2000,minPos[2]-2)
	glEnd( )

	glBegin( GL_TRIANGLES )
	glNormal3d(0,0,1)
	glVertex3f(-2000,2000,minPos[2]-2)
	glVertex3f(2000,-2000,minPos[2]-2)
	glVertex3f(2000,2000,minPos[2]-2)
	glEnd( )


	# Draw grid on floor

	gridSpacing=20
	gridSize=100 
	for i in range(gridSize):
		# lines parallel to x-axis
		glColor3f( 1, 1, 1 )

		glBegin( GL_LINES )
		glNormal3d(0,0,1)
		glVertex3f( -1000, (i-gridSize/2)*gridSpacing, minPos[2]-1 )
		glVertex3f( 1000, (i-gridSize/2)*gridSpacing, minPos[2]-1 )
		glEnd( )

		# lines parallel to y-axis
		glColor3f( 1, 1, 1 )

		glBegin( GL_LINES )
		glNormal3d(0,0,1)
		glVertex3f( (i-gridSize/2)*gridSpacing, -1000, minPos[2]-1 )
		glVertex3f( (i-gridSize/2)*gridSpacing, 1000, minPos[2]-1 )
		glEnd( )


	# Save as PNG image
	saveBufferAsPNG(outputfile)


	# glut main loop unstoppable...
	sys.exit(0)

		

def main( ):
	
	size = 800
	global inputfile, outputfile


	# Parse parameters
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:o:s:")
	except getopt.GetoptError as err:
		print str(err) 
		sys.exit(2)

	for o, a in opts:
		if o == "-i":
		    inputfile = a
		elif o == "-o":
		    outputfile = a
		elif o == "-s":
		    size = int(a)
		else:
		   	assert False, "unhandled option"

	if inputfile == "" or outputfile == "": 		
		print "Usage: "+sys.argv[0]+" -i [Input STL File] -o [Output PNG File] (-s SIZE)\n"
		exit(-1)
	
	gl_init(size, size) 

	glutMainLoop()

		

if __name__ == '__main__':
	main( )

