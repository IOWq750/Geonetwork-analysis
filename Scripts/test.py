layerDefinition = layer.GetLayerDefn()
fieldTypeCode = layerDefinition.GetFieldDefn(stats_dict[stats]).GetType()
fieldType = layerDefinition.GetFieldDefn(stats_dict[stats]).GetFieldTypeName(fieldTypeCode)
print(fieldType)
if fieldType in ['OFTReal', 'OFTInt']: