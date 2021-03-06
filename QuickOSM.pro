SOURCES = __init__.py \
	quick_osm.py \
	ProcessingQuickOSM/QuickOSMAlgorithmProvider.py \
	ProcessingQuickOSM/API/XapiQueryGeoAlgorithm.py \
	ProcessingQuickOSM/API/OverpassQueryGeoAlgorithm.py \
	ProcessingQuickOSM/API/NominatimQueryGeoAlgorithm.py \
	ProcessingQuickOSM/Tools/ReadIniFileGeoAlgorithm.py \
	ProcessingQuickOSM/Tools/ListIniFilesGeoAlgorithm.py \
	ProcessingQuickOSM/Tools/GetFirstFieldGeoAlgorithm.py \
	ProcessingQuickOSM/Tools/QueryFactoryGeoAlgorithm.py \
	ProcessingQuickOSM/Tools/ReadIniFilePathGeoAlgorithm.py \
	ProcessingQuickOSM/Parser/OsmParserGeoAlgorithm.py \
	ProcessingQuickOSM/Parser/OsmMemberParserGeoAlgorithm.py \
	Controller/Process.py \
	CoreQuickOSM/Actions.py \
	CoreQuickOSM/ExceptionQuickOSM.py \
	CoreQuickOSM/FileQuery.py \
	CoreQuickOSM/FileQueryWriter.py \
	CoreQuickOSM/QueryFactory.py \
	CoreQuickOSM/Tools.py \
	CoreQuickOSM/API/ConnexionOAPI.py \
	CoreQuickOSM/API/ConnexionXAPI.py \
	CoreQuickOSM/API/Nominatim.py \
	CoreQuickOSM/Parser/pghstore.py \
	CoreQuickOSM/Parser/OsmParser.py \
	CoreQuickOSM/Parser/OsmMemberParser.py \
	ui/main_window_dialog.py \
	ui/main_window.py \
	ui/my_queries_dialog.py \
	ui/my_queries.py \
	ui/osm_file_dialog.py \
	ui/osm_file.py \
	ui/query_dialog.py \
	ui/query.py \
	ui/quick_query_dialog.py \
	ui/quick_query.py \
	ui/save_query_dialog.py \
	ui/save_query.py \
	ui/QuickOSMWidget.py

TRANSLATIONS = i18n/QuickOSM_fr.ts \
	i18n/QuickOSM_ru.ts \
	i18n/QuickOSM_de.ts \
	i18n/QuickOSM_it.ts \
	i18n/QuickOSM_nl.ts \
	i18n/QuickOSM_en.ts