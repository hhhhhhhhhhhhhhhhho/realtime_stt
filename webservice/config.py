import json
# 설정을 관리하는 클래스
class Config:
    '''
    설정 파일을 관리하는 클래스입니다.
    
    Returns:
    - config (dict): 설정 값들을 담고 있는 딕셔너리.
    '''
    def __init__(self, config_file="webservice/config.json"):
        '''
        생성자 함수로, 설정 파일을 읽고 딕셔너리로 저장합니다.
        
        Arguments:
        - config_file (str): 설정 파일 경로. 기본값은 "config.json".
        '''
        with open(config_file, "r") as file:
            self.config = json.load(file)

    def get(self, key):
        '''
        설정 파일에서 특정 키의 값을 반환합니다.
        
        Arguments:
        - key (str): 찾고자 하는 설정 키.
        
        Returns:
        - value: 설정 값 (없으면 None 반환).
        '''
        return self.config.get(key, None)


