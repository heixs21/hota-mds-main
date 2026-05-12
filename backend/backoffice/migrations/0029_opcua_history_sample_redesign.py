# Generated manually for OpcUaHistorySample redesign (drops old columns, new schema).

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


def forwards_clear(apps, schema_editor):
    OpcUaHistorySample = apps.get_model("backoffice", "OpcUaHistorySample")
    OpcUaHistorySample.objects.all().delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0028_runtimeparameterconfig_gantt_anchor_mode"),
    ]

    operations = [
        migrations.RunPython(forwards_clear, noop_reverse),
        migrations.RemoveIndex(model_name="opcuahistorysample", name="opcua_hist_ds_time_idx"),
        migrations.RemoveField(model_name="opcuahistorysample", name="node_id"),
        migrations.RemoveField(model_name="opcuahistorysample", name="value"),
        migrations.RemoveField(model_name="opcuahistorysample", name="quality"),
        migrations.RemoveField(model_name="opcuahistorysample", name="sampled_at"),
        migrations.AlterField(
            model_name="opcuahistorysample",
            name="data_source",
            field=models.ForeignKey(
                db_comment="OPC UA 数据源配置ID",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="opcua_history_samples",
                to="backoffice.datasourceconfig",
                verbose_name="数据源配置",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="area",
            field=models.ForeignKey(
                blank=True,
                db_comment="从设备抄录的区域，便于按厂区筛选",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="opcua_history_samples",
                to="backoffice.area",
                verbose_name="区域（冗余）",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="device",
            field=models.ForeignKey(
                blank=True,
                db_comment="本次读取上下文设备；无法确定时为空",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="opcua_history_samples",
                to="backoffice.device",
                verbose_name="关联设备",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="duration_ms",
            field=models.PositiveIntegerField(
                blank=True,
                db_comment="read_opcua_nodes 耗时",
                null=True,
                verbose_name="读耗时毫秒",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="failure_summary",
            field=models.CharField(
                blank=True,
                db_comment="短摘要；完整信息在 payload",
                default="",
                max_length=512,
                verbose_name="失败摘要",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="fetched_at",
            field=models.DateTimeField(
                db_comment="OPC 读完成时间",
                default=timezone.now,
                verbose_name="数据获取时间",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="item_count",
            field=models.PositiveSmallIntegerField(
                blank=True,
                db_comment="opcuaRead.items 长度",
                null=True,
                verbose_name="节点条数",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="offline",
            field=models.BooleanField(
                db_comment="与 OpcUaReadResult.offline 一致",
                default=True,
                verbose_name="是否连接级离线",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="payload",
            field=models.JSONField(
                db_comment="含 opcuaRead 与 schemaVersion 等",
                default=dict,
                verbose_name="读数明细 JSON",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="payload_bytes",
            field=models.PositiveIntegerField(
                blank=True,
                db_comment="JSON UTF-8 序列化长度",
                null=True,
                verbose_name="payload 字节数",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="payload_version",
            field=models.SmallIntegerField(
                db_comment="与 payload.schemaVersion 对齐",
                default=1,
                verbose_name="payload 结构版本",
            ),
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="read_ok",
            field=models.BooleanField(
                db_comment="与 OpcUaReadResult.ok 一致",
                default=False,
                verbose_name="读是否成功",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="opcuahistorysample",
            name="trigger",
            field=models.CharField(
                db_comment="display_realtime/device_status_probe/admin_test_connection/script 等",
                default="legacy",
                max_length=64,
                verbose_name="写入来源",
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="opcuahistorysample",
            options={
                "ordering": ["-fetched_at", "-id"],
                "verbose_name": "OPC UA 历史采样",
                "verbose_name_plural": "OPC UA 历史采样",
            },
        ),
        migrations.AddIndex(
            model_name="opcuahistorysample",
            index=models.Index(fields=["data_source", "-fetched_at"], name="opcua_hist_ds_time_idx"),
        ),
        migrations.AddIndex(
            model_name="opcuahistorysample",
            index=models.Index(fields=["data_source", "read_ok", "-fetched_at"], name="opcua_hist_ds_ok_time_idx"),
        ),
        migrations.AddIndex(
            model_name="opcuahistorysample",
            index=models.Index(fields=["device", "-fetched_at"], name="opcua_hist_dev_time_idx"),
        ),
    ]
