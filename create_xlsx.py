# backend/create_excel.py
import pandas as pd

# 데이터 시트 생성
data = {
    'id': [1, 2, 3],
    'filepath': ['image1.png', 'image2.png', 'image3.png'],
    'other_info': ['info1', 'info2', 'info3']
}
data_df = pd.DataFrame(data)

# 메타 정보 시트 생성
meta_data = {
    'col_id': ['id', 'filepath', 'other_info'],
    'col_name': ['ID', 'File Path', 'Other Info'],
    'hide': [False, False, True]
}
meta_df = pd.DataFrame(meta_data)

# Excel 파일로 저장
file_path = '../data/fecal/infos.xlsx'
with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    data_df.to_excel(writer, sheet_name='infos', index=False)
    meta_df.to_excel(writer, sheet_name='meta', index=False)

print(f"Excel 파일이 생성되었습니다: {file_path}")