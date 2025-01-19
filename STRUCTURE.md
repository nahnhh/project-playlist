project-playlist
├── #debug
├── audio-extract
│   ├── artist_prefixes.py
│   ├── build_db.py 
│   ├── features_compute.py 
│   ├── features_extract.py 	
│   ├── instgroups.py
│   ├── md_edit.py 
│   ├── md_extract.py 
│   └── uid_gen.py 	
├── interface/
│   ├── display.py 						# DisplayFormatter
│   ├── editor.py 							# EditorInterface
│   ├── prompt_input.py 					# InputHandler
│   └── ui.py								# UserInterface
├── search_engine/
│   ├── playlist.py						# 
│   ├── search.py 							# 
├── track_connections/
│   ├── color_map.py 						# 
│   ├── prep_pca_viz.py 					# 
│   ├── track_connections.txt 			# (auto-generated)