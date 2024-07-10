# -*- coding: utf-8 -*-

"""
/***************************************************************************
 GpxMaker
                                 A QGIS plugin
 This plugin export GPX files for GARMIN® devices.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-05-31
        copyright            : (C) 2024 by Sanda Takeru
        email                : takeru_sanda999@maff.go.jp
 ***************************************************************************/

"""

__author__ = 'Sanda Takeru'
__date__ = '2024-05-31'
__copyright__ = '(C) 2024 by Sanda Takeru'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterVectorLayer, QgsProcessingParameterString,
                       QgsProcessingParameterField, QgsProcessingParameterBoolean,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterFileDestination, QgsWkbTypes,
                       QgsVectorLayer, QgsVectorFileWriter,
                       QgsProject)
import processing


class GpxMakerAlgorithm(QgsProcessingAlgorithm):
    # Translated and improved variable names for clarity
    VECTOR_LAYER = 'VECTOR_LAYER'
    DISPLAY_NAME = 'DISPLAY_NAME'
    DISSOLVE_FEATURES = 'DISSOLVE_FEATURES'
    NAME_FIELD = 'NAME_FIELD'
    GPX_OUTPUT = 'GPX_OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.VECTOR_LAYER, 'Vector Layer - Convert to GPX', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterString(self.DISPLAY_NAME, 'Name on Device - 30 Characters or Less Recommended', multiLine=False, defaultValue='Display Name'))
        
        param = QgsProcessingParameterBoolean(self.DISSOLVE_FEATURES, 'Do Not Dissolve Features', defaultValue=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        param = QgsProcessingParameterField(self.NAME_FIELD, 'Name Field - Not Blank, when you checked "Do Not Dissolve Features".', type=QgsProcessingParameterField.String, parentLayerParameterName=self.VECTOR_LAYER, allowMultiple=False, defaultValue=None, optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # Restrict the GPX parameter to '*.gpx' files
        self.addParameter(QgsProcessingParameterFileDestination(self.GPX_OUTPUT, 'GPX Output', fileFilter='GPX files (*.gpx)', defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(6, model_feedback)
        results = {}
        outputs = {}

        # Decision making based on layer properties
        layer = self.parameterAsVectorLayer(parameters, self.VECTOR_LAYER, context)
        layer_type = layer.geometryType()
        feature_count = layer.featureCount() 

        # Check if the layer has features
        if feature_count == 0:
            error_msg = 'Layer has no feature. Exiting process.'
            feedback.reportError(error_msg)
            raise Exception(error_msg)
        
        # Check if 'DISSOLVE_FEATURES' is True and 'NAME_FIELD' is None or empty
        if parameters[self.DISSOLVE_FEATURES] and (parameters[self.NAME_FIELD] is None or parameters[self.NAME_FIELD].strip() == ''):
            error_msg = "Error: 'NAME_FIELD' cannot be empty when 'DISSOLVE_FEATURES' is True."
            feedback.reportError(error_msg)
            raise Exception(error_msg)

        # Main
        try:
            # Set properties
            dissolve = self.parameterAsBool(parameters, self.DISSOLVE_FEATURES, context)
            name_value = '\"' + parameters[self.NAME_FIELD] + '\"' if dissolve else "\'" + parameters[self.DISPLAY_NAME] + "\'"

            # Fix geometries
            alg_params = {
                'INPUT': parameters[self.VECTOR_LAYER],
                'METHOD': 1,  # Structure
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['FixGeometries'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            next_input = outputs['FixGeometries']['OUTPUT']
            feedback.setCurrentStep(1)

            if feedback.isCanceled():
                return {}

            # Convert polygons to lines if necessary
            if layer_type == QgsWkbTypes.PolygonGeometry:
                alg_params = {
                    'INPUT': next_input,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['PolygonsToLines'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                next_input = outputs['PolygonsToLines']['OUTPUT']
                feedback.setCurrentStep(2)

            # Dissolve features if necessary
            if (not dissolve) and (not layer_type == QgsWkbTypes.PointGeometry):
                alg_params = {
                    'FIELD': [''],
                    'INPUT': next_input,
                    'SEPARATE_DISJOINT': False,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Dissolve'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                next_input = outputs['Dissolve']['OUTPUT']
                feedback.setCurrentStep(3)

            # Multipart to singleparts if layer_type == PointGeometry
            if layer_type == QgsWkbTypes.PointGeometry:
                alg_params = {
                    'INPUT' : next_input,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['MultitpartToSingleparts'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                next_input = outputs['MultitpartToSingleparts']['OUTPUT']
                feedback.setCurrentStep(4)

            # Refactor fields
            alg_params = {
                'FIELDS_MAPPING': [{'expression': name_value , 'name': 'name', 'type': 10,'type_name': 'text'}],
                'INPUT': next_input,
                'OUTPUT': parameters[self.GPX_OUTPUT]
            }
            outputs['RefactorFields'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            feedback.setCurrentStep(5)

            output_path = outputs['RefactorFields']['OUTPUT']
            output_layer = QgsVectorLayer(output_path, 'Refactored Layer', 'ogr')

            # Write output with GPX options
            vector_options = QgsVectorFileWriter.SaveVectorOptions()
            vector_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            vector_options.fileEncoding = 'UTF-8'
            vector_options.datasourceOptions = {'GPX_USE_EXTENSIONS': 'YES'}
            vector_options.layerOptions = {'FORCE_GPX_TRACKS': 'YES'}

            QgsVectorFileWriter.writeAsVectorFormatV2(
                layer=output_layer,
                fileName=parameters[self.GPX_OUTPUT],
                transformContext=QgsProject.instance().transformContext(),
                options=vector_options
            )

            results[self.GPX_OUTPUT] = parameters[self.GPX_OUTPUT]
            return results
        except Exception as e:
            feedback.reportError(str(e))
            raise

    def name(self):
        return 'Make GPX File'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return None

    def groupId(self):
        return None

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GpxMakerAlgorithm()
