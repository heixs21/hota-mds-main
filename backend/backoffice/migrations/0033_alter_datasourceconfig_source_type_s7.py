from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0032_alter_opcuahistorysample_table_comment_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datasourceconfig",
            name="source_type",
            field=models.CharField(
                choices=[
                    ("opcua", "OPCUA"),
                    ("modbus_tcp", "Modbus TCP"),
                    ("s7", "S7 PLC"),
                    ("sap_rfc", "SAP RFC"),
                    ("database", "数据库"),
                    ("repair", "报修系统"),
                    ("custom", "自定义"),
                ],
                db_comment="数据源类型；opcua/modbus_tcp/s7/sap_rfc等",
                max_length=32,
                verbose_name="数据源类型",
            ),
        ),
    ]
