#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from datetime import datetime

from api.db import StatusEnum
from api.db.db_models import DB, UserAccessToken
from api.db.services.common_service import CommonService
from api.utils import current_timestamp, datetime_format


class UserAccessTokenService(CommonService):
    model = UserAccessToken

    @classmethod
    @DB.connection_context()
    def create_token(cls, user_id, token, login_channel=None):
        data = {
            "user_id": user_id,
            "token": token,
            "status": StatusEnum.VALID.value,
        }
        if login_channel:
            data["login_channel"] = login_channel
        return cls.insert(**data)

    @classmethod
    @DB.connection_context()
    def revoke_token(cls, token):
        return cls.model.update({
            "status": StatusEnum.INVALID.value,
            "update_time": current_timestamp(),
            "update_date": datetime_format(datetime.now()),
        }).where(
            cls.model.token == token
        ).execute()

    @classmethod
    @DB.connection_context()
    def get_user_id_by_token(cls, token):
        if not token or not str(token).strip():
            return None
        record = cls.model.select(cls.model.user_id).where(
            cls.model.token == token,
            cls.model.status == StatusEnum.VALID.value,
        ).first()
        return record.user_id if record else None

    @classmethod
    @DB.connection_context()
    def touch_token(cls, token):
        return cls.model.update({
            "update_time": current_timestamp(),
            "update_date": datetime_format(datetime.now()),
        }).where(
            cls.model.token == token,
            cls.model.status == StatusEnum.VALID.value,
        ).execute()
