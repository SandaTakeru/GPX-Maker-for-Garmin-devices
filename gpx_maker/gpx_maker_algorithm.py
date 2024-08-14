# -*- coding: utf-8 -*-

__author__ = 'Sanda Takeru'
__date__ = '2024-05-31'
__copyright__ = '(C) 2024 by Sanda Takeru'
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

# Constants for the algorithm parameters
VECTOR_LAYER = 'VECTOR_LAYER'
DISPLAY_NAME = 'DISPLAY_NAME'
NAME_FIELD = 'NAME_FIELD'
GPX_OUTPUT = 'GPX_OUTPUT'

class GpxMakerAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        # Add parameters for the algorithm
        self.addParameter(QgsProcessingParameterVectorLayer(VECTOR_LAYER, 'Vector Layer - Convert to GPX', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterString(DISPLAY_NAME, 'Name on Device - 30 Characters or Less Recommended.', multiLine=False, defaultValue='Display Name'))

        param = QgsProcessingParameterField(NAME_FIELD, 'Name Field - If setting this, features will not be dissolved.', type=QgsProcessingParameterField.String, parentLayerParameterName=VECTOR_LAYER, allowMultiple=False, defaultValue=None, optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # Restrict the GPX parameter to '*.gpx' files
        self.addParameter(QgsProcessingParameterFileDestination(GPX_OUTPUT, 'GPX Output', fileFilter='GPX files (*.gpx)', defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(6, model_feedback)
        results = {}
        outputs = {}

        # Decision making based on layer properties
        layer = self.parameterAsVectorLayer(parameters, VECTOR_LAYER, context)
        layer_type = layer.geometryType()
        feature_count = layer.featureCount() 

        # Check if the layer has features
        if feature_count == 0:
            error_msg = 'The layer "{}" has no features. Exiting process.'.format(layer.name())
            feedback.reportError(error_msg)
            raise Exception(error_msg)
      
        # Set properties
        if parameters[NAME_FIELD]:
            name_value = "\"" + parameters[NAME_FIELD] + "\""
            dissolve = False
        else:
            name_value = '\'' + parameters[DISPLAY_NAME] + '\''
            dissolve = True
        
        # Main
        try:
            # Fix geometries
            alg_params = {
                'INPUT': parameters[VECTOR_LAYER],
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
            if (dissolve) and (not layer_type == QgsWkbTypes.PointGeometry):
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
                'OUTPUT': parameters[GPX_OUTPUT]
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
                fileName=parameters[GPX_OUTPUT],
                transformContext=QgsProject.instance().transformContext(),
                options=vector_options
            )

            results[GPX_OUTPUT] = parameters[GPX_OUTPUT]
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
