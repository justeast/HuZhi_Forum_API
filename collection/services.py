from django.db import transaction
from collection.models import Collection


def create_collection(user, validated_data: dict) -> Collection:
    """
    创建收藏夹
    """
    with transaction.atomic():
        collection = Collection.objects.create(
            owner=user,
            **validated_data
        )
    return collection


def update_collection(collection: Collection, validated_data: dict) -> Collection:
    """
    更新收藏夹
    """
    with transaction.atomic():
        for key, value in validated_data.items():
            setattr(collection, key, value)
        collection.save()
    return collection


def toggle_collect_answer(collection: Collection, answer) -> tuple:
    """
    收藏/取消收藏回答（toggle操作）
    返回: (is_collected, answer_count)
        - is_collected: True=已收藏, False=已移除
        - answer_count: 更新后的收藏数量
    """
    with transaction.atomic():
        # 判断是否已收藏
        if collection.answers.filter(id=answer.id).exists():
            # 已收藏 -> 移除
            collection.answers.remove(answer)
            is_collected = False
        else:
            # 未收藏 -> 添加
            collection.answers.add(answer)
            is_collected = True
        
        # 获取更新后的数量
        answer_count = collection.answers.count()
        
        return is_collected, answer_count
