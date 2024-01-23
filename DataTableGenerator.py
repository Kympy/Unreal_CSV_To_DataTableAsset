import csv

import unreal
import sys
import os

#프로젝트 명
project_name = "RottenPotato"

# 데이터 테이블 클래스
asset_class = unreal.DataTable

# 데이터 테이블 에셋 저장 경로
asset_path = "/Game/Table"

# CSV 파일이 존재하는 폴더 경로
csv_folder = unreal.SystemLibrary.get_project_directory() + "CSV"

# c++ struct 를 저장할 폴더 경로 ->
struct_save_folder = unreal.SystemLibrary.get_project_directory() + "Source/RottenPotato/Public/Table"


# struct_path : ex) "/Script/RottenPotato.TestTable"
# 데이터 테이블 에셋 생성 함수
def create_data_table_asset(csv_path, unreal_struct_path):
    print("Creating data table asset..." + " Struct path : " + unreal_struct_path)
    print("-")
    # 데이터 테이블 파일명
    asset_name = "DT_" + str(os.path.basename(csv_path)).split('.')[0]
    # 데이터 테이블 구조체
    asset_factory = unreal.DataTableFactory()
    asset_factory.struct = unreal.load_object(None, unreal_struct_path)
    if asset_factory.struct is None:
        print("Asset factory struct is none.")
        sys.exit(0)

    # CSV 를 추출해서 순 데이터만 존재하는 임시파일 생성
    origin_rows = []
    with open(csv_path, 'r') as origin:
        csv_reader = csv.reader(origin)
        id_row_index = sys.maxsize

        for index, row in enumerate(csv_reader):
            origin_rows.append(row)
            if str(row[0]).lower() == "id":
                id_row_index = index

        if id_row_index == -1:
            print("Cannot found Id column.")
            return

    raw_data_rows = []
    for index, row in enumerate(origin_rows):
        if index >= id_row_index:
            raw_data_rows.append(row)

    temp_csv_path = unreal.SystemLibrary.get_project_directory() + "Temp_TableGenerator.csv"

    with open(temp_csv_path, 'w') as temp_csv:
        for row in raw_data_rows:
            for index, data in enumerate(row):
                temp_csv.write(data)
                if index != len(row):
                    temp_csv.write(",")
            temp_csv.write("\n")

    csv_factory = unreal.CSVImportFactory()
    csv_factory.automated_import_settings.import_row_struct = asset_factory.struct

    task = unreal.AssetImportTask()
    task.filename = temp_csv_path
    task.destination_name = asset_name
    task.destination_path = asset_path
    task.replace_existing = True
    task.automated = True
    task.save = True
    task.factory = csv_factory

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    try:
        os.remove(temp_csv_path)
    except FileNotFoundError:
        return
    except Exception as e:
        print(e)

    # # 데이터 테이블 에셋 생성
    # created_asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(asset_name, asset_path, asset_class,
    #                                                                         asset_factory)
    # if created_asset is None:
    #     print("Asset creation failed.")
    #     sys.exit(0)
    # # 데이터 테이블 에셋에 CSV import
    # unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(created_asset, csv)
    # # 데이터 테이블 에셋 저장
    # unreal.EditorAssetLibrary.save_loaded_asset(created_asset)


# 개행 함수
def next_line(file):
    file.write("\n")


# 타입 선별 함수
def get_unreal_type(type):

    str_type = str(type).lower()

    if str_type == "int" or str_type == "int32":
        return "int32"
    elif str_type == "float" or str_type == "float32":
        return "float"
    elif str_type == "string" or str_type == "fstring":
        return "FString"
    elif str_type == "bool" or str_type == "boolean":
        return "bool"
    elif str_type == "vector" or str_type == "vector3":
        return "FVector"
    elif str_type == "rotator" or str_type == "rotator":
        return "FRotator"
    elif str_type == "text":
        return "FText"
    elif str_type == "color" or str_type == "coloru8":
        return "FLinearColor"


# c++ struct 생성 및 저장
def create_struct_file(csv_path):
    print("Writing C++ Struct row table...")
    print("-")
    # CSV 를 행 별로 저장
    rows = []
    # 파일 열고 행 별로 rows 에 담는다
    with open(csv_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            rows.append(row)

    # 행이 아무것도 없다면 종료
    if len(rows) == 0:
        print("CSV row count is 0")
        return None

    # Id 로 시작하는 행을 찾기 위해 초기값 -1 로 설정
    column_name_row_index = -1
    for data in rows:
        if data[0] == "Id" or str(data[0]).lower() == "id":
            column_name_row_index = rows.index(data)

    if column_name_row_index == -1:
        print("Cannot found Id column")
        return None

    type_name_list = []
    column_name_list = []

    column_name_row = rows[column_name_row_index]

    for index, column_name in enumerate(column_name_row):
        # '#' 으로 시작하는 칼럼은 추가하지 않는다.
        if not column_name.startswith("#"):
            # Id 칼럼 위 행은 타입 행이므로 -1 한 위치에서 타입 이름을 저장.
            # rows[Id 칼럼의 윗 행 인덱스][현재 열 인덱스]
            type_row = rows[column_name_row_index - 1]
            type_name_list.append(type_row[index])
            column_name_list.append(column_name)

    if len(type_name_list) != len(column_name_list):
        print("Type name count and column name count is not correct : " + len(type_name_list) + "/" + len(column_name_list))
        return None

    file_name = os.path.basename(csv_path)
    file_name = str(file_name).split('.')[0]

    with open(struct_save_folder + "/F" + file_name + ".h", 'w') as c_file:
        # 쓰기 시작
        c_file.writelines("// Copyright Parrot_Yong, MIT LICENSE\n")
        c_file.writelines("// This file is auto generated by Parrot_Yong's table generator.\n")
        next_line(c_file)
        c_file.writelines("# pragma once\n")
        next_line(c_file)
        c_file.writelines("#include \"Engine/DataTable.h\"\n")
        c_file.writelines("#include \"F" + file_name + ".generated.h\"\n")
        next_line(c_file)
        c_file.writelines("USTRUCT(Blueprintable)\n")
        c_file.writelines("struct F" + file_name + " : public FTableRowBase\n")
        c_file.writelines("{\n")
        c_file.writelines("\tGENERATED_USTRUCT_BODY()\n")
        next_line(c_file)
        c_file.writelines("public:\n")
        next_line(c_file)

        for index, value in enumerate(column_name_list):
            # id 변수는 선언하지 않는다 -> 기본적으로 Row Name 칼럼이 Id 역할을 해주기 때문.
            if str(value).lower() == "id":
                continue
            c_file.writelines("\tUPROPERTY(EditAnywhere, BlueprintReadWrite)\n")
            c_file.writelines("\t" + get_unreal_type(type_name_list[index]) + " " + str(value) + ";\n")
            next_line(c_file)

        c_file.writelines("};\n")

    # struct_path : ex) "/Script/project_name.TestTable"
    unreal_struct_path = "/Script/" + project_name + "." + file_name
    return unreal_struct_path


# 모든 CSV to Data Table 시작
def generate_all():
    print("#######   Data table generator started!     #######")
    print("######    Target CSV Folder : " + csv_folder)
    print("-")
    # csv_folder 내부의 모든 파일 리스트 검출
    file_list = os.listdir(csv_folder)
    # csv_file_list = unreal.EditorAssetLibrary.list_assets(unreal.Paths.convert_relative_path_to_full("/RottenPotato"), True, False)
    csv_file_list = []
    # CSV 가 아닌 것 걸러내기
    for file in file_list:
        if file.endswith(".csv"):
            csv_file_list.append(file)

    if len(csv_file_list) == 0:
        print("There's no CSV file in folder : " + csv_folder)
        sys.exit(0)

    print("----------- CSV File List ------------")
    print("-")
    # 반복문 시작 : 하나 씩 변환 시작
    index = 1
    for file in csv_file_list:
        print("(" + str(index) + ") " + file)
        index += 1

    print()
    for file in csv_file_list:
        print("-")
        print(":::Start making " + file + ":::")
        # csv 파일 경로 추출
        csv_file_path = os.path.join(csv_folder, file)
        # 먼저 C++ 부터 작성
        struct_result = create_struct_file(csv_file_path)
        # 작성 실패 시, 다음 CSV 타겟으로 넘어감.
        if struct_result is None:
            print("Failed to generate C++ file")
            continue

        create_data_table_asset(csv_file_path, struct_result)

# 실행
generate_all()






