import os
import json
import numpy as np
import pandas as pd

import string
import random

from .aux_fun import *


class Stations_manage:
	def __init__(self, dir_path): 
		"""
		Station manage object
		"""
		# LOAD STATIC ATRIBUTES
		self.dir_path = dir_path
		self.save_path = os.sep.join(dir_path.split(os.sep)[:-1])
		self.gnrl_dict = {"columns int search" : ['id'],
						  "columns str search" : ['nombre', 'corriente'],
						  "columns coords" : ['latitud','longitud'],
                         }
		# READ FILE
		self.full_data = self.read_file()
		
		# FIX CONTENT OF THE COLUMNS
		self.__fix_columns_data__()

		# SLICE FULL DATAFRAME
		self.data = self.full_data[self.gnrl_dict["columns int search"] + self.gnrl_dict["columns str search"] + self.gnrl_dict["columns coords"]].copy()
		self.data.reset_index(inplace=True)
		self.data.rename(columns={'index':'ID_tmp'}, inplace=True)

		# APP METHOD - EXTRACT SEARCH LIST
		self.__extract_search_list__()


	def __call__(self, search_id: str):
		'''
        Input: 
            search_data : str = value to search
		'''

		# Extract coords of the station
		coords = self.__coordssearch__(search_id)

        # Assert does not existence of the station
		if len(coords) < 1:
			return 'COLOMBIA.json', coords, 404, '', ''

        # Extract coords of the polygon
		lat_coord, lon_coord = get_zoom_coords(df  = coords, 
											   lat = self.gnrl_dict['columns coords'][0],
                                               lon = self.gnrl_dict['columns coords'][1])

        # Build station output file
		output_station_file, station_file_cont = self.__printstaiongeojson__(df=coords)

        # Build coundary output file
		output_file, boundary_file_cont = self.__printgeojson__(lat_coord=lat_coord, lon_coord=lon_coord)

		return output_file, output_station_file, 200, station_file_cont, boundary_file_cont


	# Get methods
	def get_search_list(self):
		return self.__search_list__


	# Methoda
	def read_file(self):
		data = json.load(open(self.dir_path))['features']
		df = pd.DataFrame()
		for line in data:
			line_data = line['properties']
			col_names = list(line_data.keys())
			col_data = [line_data[ii] for ii in col_names]
			tmp = pd.DataFrame(data= [col_data],
							   columns=col_names)
			df = pd.concat([df, tmp], ignore_index=True)

		for column in df.columns:
			df[column] = df[column].astype(str)

		return df


	# Hidden methods
	def __extract_search_list__(self):
		rv = self.full_data[self.gnrl_dict['columns int search'] + self.gnrl_dict['columns str search']].copy()
		rv = np.unique(rv.values.ravel('F'))
		self.__search_list__ = rv.tolist()


	def __fix_columns_data__(self):
		# Change for str columns
		for col_name in self.gnrl_dict['columns str search']:
			self.full_data[col_name] = self.full_data[col_name].str.lower()
			self.full_data[col_name] = list(map(lambda x: x.replace('á', 'a'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('é', 'e'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('í', 'i'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('ó', 'o'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('ú', 'u'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('ñ', 'n'), self.full_data[col_name]))
			self.full_data[col_name] = self.full_data[col_name].str.upper()
			self.full_data[col_name] = self.full_data[col_name].str.lstrip()
			self.full_data[col_name] = self.full_data[col_name].str.rstrip()

		for col_name in self.gnrl_dict['columns int search']:
			self.full_data[col_name] = list(map(lambda x : str(int(float(x))), self.full_data[col_name]))


	def __coordssearch__(self, search_id):

		# Identify type of input
		try:
			# Search by code
			seach_case = 'int'
			search_id = str(int(search_id))
			columns_to_search = self.gnrl_dict['columns int search']
		except:
			# Search by name
			search_case = 'name'
			search_id = str(search_id).upper()
			columns_to_search = self.gnrl_dict['columns str search']

        
        # Extract column to search
		search_df = pd.DataFrame()
		for col in columns_to_search:
			tmp_df = pd.DataFrame()
			tmp_df['ID_tmp'] = self.data['ID_tmp']

           
			if seach_case == 'int':
				tmp_df['values'] = self.data[col].astype(str)
			elif seach_case == 'str':
				# TODO: Add decodifficator for spañish when by name is used
				tmp_df['values'] = self.data[col].astype(str)
			else:
				# TODO: Add search by lat,lon
				pass

			search_df = pd.concat([search_df, tmp_df], ignore_index=True)

		idtmp_to_search = search_df.loc[search_df['values'] == search_id]

		valids = self.data[columns_to_search].isin(idtmp_to_search['values'].values).values
		rv = self.data.loc[valids].copy()

		return rv


	def __printstaiongeojson__(self, df):

		lon = self.gnrl_dict['columns coords'][1]
		lat = self.gnrl_dict['columns coords'][0]

		# TODO: Add variable name file for multyple user. And remove path
		# pathdir and name file
		# file_name = str(uuid.uuid4()) + '.json'
		file_name = 'station_geojson' + '.json'
		file_path = os.sep.join([self.save_path, file_name])


		# Build json
		feature = []
		for _, row in df.iterrows():
			feature.append({'type' : "Feature",
							"geometry" : {"type" : "Point",
										  "coordinates":[row[lon], row[lat]]}})
		json_file = {"type" : "FeatureCollection",
					 "features" : feature}


		with open(file_path, 'w', encoding='utf-8') as f:
			json.dump(json_file, f, ensure_ascii=False, indent=4)

		return file_name, json_file


	def __printgeojson__(self, lat_coord, lon_coord):
        
		# TODO: Add variable name file for multyple user. And remove path
		# pathdir and name file
		# file_name = str(uuid.uuid4()) + '.json'
		file_name = 'boundary_geojson' + '.json'
		file_path = os.sep.join([self.save_path, file_name])

		# Print json
		json_file = {"type":"FeatureCollection", 
                    "features": [{ "type" : "Feature",
                                   "geometry" : { "type"       : "Polygon",
                                                  "coordinates" : [[[lon_coord[0], lat_coord[0]],
                                                                    [lon_coord[1], lat_coord[1]],
                                                                    [lon_coord[3], lat_coord[3]],
                                                                    [lon_coord[2], lat_coord[2]]]]
                                                }
                                }]
                    }


		with open(file_path, 'w', encoding='utf-8') as f:
			json.dump(json_file, f, ensure_ascii=False, indent=4)

		return file_name, json_file

####################################################################################
class SearchList:
    def __init__(self, file_path, main_cols):
        '''
        Build search list
        Input: 
            file_path : str -> Path of the GeoJSON file
            main_cols : dict ->Dictionary with columns to fix and work.
            e.p. :
                main_col = dict([('int column name', ['names', 'columns', 'here']),
                                 ('str column name', ['names', 'columns', 'here'])])
        '''
        self.geoJSON, self.crs_dict = self.__read_file__(file_path)
        self.main_cols = main_cols

        self.__fix_columns__()


    def get_df_geoJSON(self):
        '''
        Get dataframe with geoJSON data
        '''
        return self.geoJSON


    def get_search_list(self):
        '''
        Get search list of the columns given
        '''
        rv = self.geoJSON[self.main_cols['int column name'] + self.main_cols['str column name']].copy()
        rv = np.unique(rv.values.ravel('F'))
        return rv.tolist()


    def __fix_columns__(self):
        '''
        Fix the values of the columns depending of: integer value or string value
        '''
		# Change for str columns
        for col_name in self.main_cols['str column name']:
            
            # Replace null values
            self.geoJSON[col_name].fillna(value='na', inplace = True)

            # Replace other letters (ES)
            self.geoJSON[col_name] = self.geoJSON[col_name].str.lower()
            self.geoJSON[col_name] = list(map(lambda x: x.replace('á', 'a'), self.geoJSON[col_name]))
            self.geoJSON[col_name] = list(map(lambda x: x.replace('é', 'e'), self.geoJSON[col_name]))
            self.geoJSON[col_name] = list(map(lambda x: x.replace('í', 'i'), self.geoJSON[col_name]))
            self.geoJSON[col_name] = list(map(lambda x: x.replace('ó', 'o'), self.geoJSON[col_name]))
            self.geoJSON[col_name] = list(map(lambda x: x.replace('ú', 'u'), self.geoJSON[col_name]))
            # self.geoJSON[col_name] = list(map(lambda x: x.replace('ñ', 'n'), self.geoJSON[col_name]))
            self.geoJSON[col_name] = list(map(lambda x: x.replace('_', ' '), self.geoJSON[col_name]))
            self.geoJSON[col_name] = self.geoJSON[col_name].str.upper()
            self.geoJSON[col_name] = self.geoJSON[col_name].str.lstrip()
            self.geoJSON[col_name] = self.geoJSON[col_name].str.rstrip()

		# Change for int columns
        for col_name in self.main_cols['int column name']:
            self.geoJSON[col_name] = list(map(lambda x : str(int(float(x))), self.geoJSON[col_name]))


    @staticmethod
    def __read_file__(file_path):
        '''
        Read geojson as dataframe with type and coordinates column
        Input:
            file_path : str -> GeoJSON path.
        Return:
            df : pd.DataFrame() -> GeoJSON cont. 
        '''
        data = json.load(open(file_path))['features']
        crs_dict = json.load(open(file_path))['crs']
        df = pd.DataFrame()

        for num, line in enumerate(data):
            # Extract features
            col_feat = pd.DataFrame.from_dict(line['properties'], orient='index').T

            # Fix feature columns
            if 'type' in col_feat:
                print('"type" is a column name restricted for GeoJSON. Will be removed.')
                col_feat.remove('type')
            if 'coordinates' in col_feat:
                print('"coordinate" is a column name restricted for GeoJSON. Will be removed.')
                col_feat.remove('coordinates')

            # Extract localization data
            col_loca = pd.DataFrame.from_dict(line['geometry'], orient='index').T

            # Extract mean of x and y data
            if 'Point' == col_loca['type'].values:
                tmp_numpy_array = np.mean(np.asmatrix(col_loca['coordinates'].values[0]), axis=0).tolist()
            elif 'MultiLineString' == col_loca['type'].values:
                tmp_numpy_array = np.mean(np.asmatrix(col_loca['coordinates'].values[0][0]), axis=0).tolist()
            else:
                continue

            col_loca['mean_coordinates_0'] = tmp_numpy_array[0][0]
            col_loca['mean_coordinates_1'] = tmp_numpy_array[0][1]

            line_df = pd.concat([col_feat, col_loca], axis=1)
            df = pd.concat([df, line_df], axis=0)
        
        df.reset_index(inplace=True, drop=True)
        return df, crs_dict


class SearchManage(SearchList):
    def __init__(self, file_path : str, main_cols : dict, search_id : str):
        '''
        Make the search in the database
        Input:
            file_path : str -> Path of the GeoJSON file.
            main_cols : dict ->Dictionary with columns to fix and work.
            e.p. :
                main_col = dict([('int column name', ['names', 'columns', 'here']),
                                 ('str column name', ['names', 'columns', 'here'])])
            search_id : str -> String to search in the database.
        '''
        self.search_id = str(search_id)
        self.__random_col_name__()
        super().__init__(file_path=file_path, main_cols=main_cols)
        

        
    def get_data_for_code(self):
        '''
        Get data for search data
        '''
        # List of all columns to search
        main_cols_list = [elm for sublst in list(self.main_cols.values()) for elm in sublst]

        # Split dataframe only with main columns
        df = super().get_df_geoJSON()
        df = df[main_cols_list].copy()
        df.reset_index(inplace=True)
        df.rename(columns={'index':self.__rnd_col_n__}, inplace=True)

        # Get geoJSON data selected
        data = self.__coordssearch__(data=df)

        # Get main geoJSON for plot in map
        boundary_geoJSON_cont = self.__boundary_extract__(data=data)
        # Worked but removed for webside performance and time charge
        polygon_geoJSON_cont = self.__polygons_extract__(data=data)

        return boundary_geoJSON_cont, polygon_geoJSON_cont


    def __boundary_extract__(self, data):
        '''
        Extract boundary json object
        '''
        # Extract boundary coords
        x_min = data['mean_coordinates_0'].min() # Lng ([0] , 0)
        x_max = data['mean_coordinates_0'].max() # Lng ([1] , 1)
        y_min = data['mean_coordinates_1'].min() # Lat (0 , [0])
        y_max = data['mean_coordinates_1'].max() # Lat (1 , [1])
        
        # Built geoJSON object
        json_file = {"type":"FeatureCollection",
                     "crs": self.crs_dict,
                     "features": [{ "type" : "Feature",
                                    "properties" : {},
                                    "geometry" : { "type"       : "Polygon",
                                                  "coordinates":[[[x_min, y_min],
                                                                  [x_min, y_max],
                                                                  [x_max, y_max],
                                                                  [x_max, y_min]]],
                                                }
                                 }]
                    }

        return json_file


    def __polygons_extract__(self, data):
        '''
        Extract geojson object for map
        '''
        def build_json_file(data):

            features_list = []

            for _, row in data.iterrows():

                features_list.append({ "type" : "Feature",
                                        "properties" : {},
                                        "geometry" : { "type"     : row['type'],
                                                    "coordinates" : row['coordinates'],
                                                    }
                                    })

            return features_list
        
        features = build_json_file(data=data)
        
        json_file = {"type": "FeatureCollection",
                     "crs": self.crs_dict,
                     "features" : features,
                     }

        return json_file


    def __coordssearch__(self, data):
        '''
        Search by coord in data
        '''
        # Identify type of input
        try:
            # Search by code
            search_case = 'int'
            search_id = str(int(self.search_id))
            columns_to_search = self.main_cols['int column name']
        except:
            # Search by name
            search_case = 'str'
            search_id = str(self.search_id).upper()
            columns_to_search = self.main_cols['str column name']

        
        # Extract column to search
        search_df = pd.DataFrame()
        for col in columns_to_search:
            tmp_df = pd.DataFrame()
            tmp_df[self.__rnd_col_n__] = data[self.__rnd_col_n__]

           
            if search_case == 'int':
                tmp_df['values'] = data[col].astype(str)
            elif search_case == 'str':
                # TODO: Add decodifficator for spañish when by name is used
                tmp_df['values'] = data[col].astype(str)
            else:
                # TODO: Add search by lat,lon
                pass

            search_df = pd.concat([search_df, tmp_df], ignore_index=True)

        idtmp_to_search = search_df.loc[search_df['values'] == search_id]

        valids = data[columns_to_search].isin(idtmp_to_search['values'].values).values
        full_data = super().get_df_geoJSON()
        rv = full_data.loc[valids, ['type', 'coordinates', 'mean_coordinates_0', 'mean_coordinates_1']].copy()
        rv.reset_index(inplace=True, drop=True)

        return rv


    def __random_col_name__(self):
        '''
        Built column data
        '''
        letters = string.ascii_lowercase
        self.__rnd_col_n__ = ''.join(random.choice(letters) for i in range(5))


def get_search_list(*args, **kwards):
    '''
    FRONTEND
    Build list of the data for search
    See: SearchList.get_search_list()
    '''
    rv = SearchList(*args, **kwards)
    return rv.get_search_list()


def get_geoJSON_from_id(*args, **kwards):
    '''
    BACKEND
    Return json objects from data and identify code/name
    See: SearchManage.get_data_for_code()
    '''
    rv = SearchManage(*args, **kwards)
    return rv.get_data_for_code()

