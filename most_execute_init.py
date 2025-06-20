class InsertRawdata(Resource):
  def port(selt):
    try:
      parser = reqparse.RequestParser()
      parser.add_argument("RAWDATA_DICT')
      args = json.loads(json.dumps(parser.parse_args()))
      base_info_dict = json.loads(args["RAWDATA_DICT"])["BASE_INFO_DICT"]
      input_value_list = json.loads(args["RAWDATA_DICT"])["INPUT_VALUE_LIST"]
      output_value_list = json.loads(args["RAWDATA_DICT"])["OUTPUT_VALUE_LIST"]
  
      MOST_EXECUTE.INSERT_RAWDATA(base_info_dict , input_value_list, output_value_list)
    
    excetp Exception as e:
      return str(traceback.format_exc()), HTTPStatus.INTERNAL_SERVER_ERROR
    else:
      return None
