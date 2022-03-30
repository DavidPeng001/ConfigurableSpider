
String.prototype.format = function () {
    const e = arguments;
    return !!this && this.replace(/\{(\d+)\}/g, function (t, r) {
        return e[r] ? e[r] : t;
    })
};

$(function () {
    var toolsComponent = Vue.extend({
        props: ['tableId' ,'index', 'loc', 'name', 'type', 'value', 'next'],
        template: `
            <div class="btn-toolbar" role="toolbar">
                <button class="btn btn-primary btn-sm" @click="parserRowAdd(tableId, index, loc, name)">增加同级元素</button>
                <button class="btn btn-default btn-sm" @click="parserRowAddChild(tableId, index, loc, name)">增加子元素</button>
                <button class="btn btn-danger btn-sm" @click="parserRowRemove(tableId, index)">删除</button>
            </div>
        `,
        methods: {
            parserRowAdd: function (tableId, index, loc) {
                console.log(tableId)
                $(tableId).bootstrapTable('insertRow', {
                    index: $(tableId).bootstrapTable('getData').length,
                    row: {
                        loc: loc,
                        name: '',
                        type: 'xpath',
                        value: '',
                        next: ''
                    }
                })
            },

            parserRowAddChild: function (tableId, index, loc, name) {
                console.log(name)
                if (name == '{3}') {
                    alert('请先设置字段名称')
                    return
                }
                $(tableId).bootstrapTable('insertRow', {
                    index: index + 1,
                    row: {
                        loc: loc + '.' + name,
                        name: '',
                        type: 'xpath',
                        value: '',
                        next: ''
                    }
                })
            },
            parserRowRemove: function (tableId, index) {
                var data = $(tableId).bootstrapTable('getData')
                if (data.length <= 1) {
                    alert('禁止删除最后一行数据')
                    return
                }
                data.splice(index, 1)
                $(tableId).bootstrapTable('load', data)
            }
        }
    })

    var app = new Vue({
        el: '#wrap',
        delimiters: ['[[', ']]'],
        data: {
            pageIndex: 0,
            styleActive: 'active',
            styleEmpty: '',
            savedConfigItems: ['test'],
            configName: '',
            totalConfig : {
                common: {
                    is_stacic : false,
                    deepth_limit: -1,
                    external_def: ''
                    
                },
                stages: [
                    {   
                        name: '',
                        header: {
                            external: [''],
                            loop: [{
                                "key": "",
                                "value": ""
                            }],
                        },
                        request: {
                            url: '',
                            method: 'GET',
                            headers: [{
                                "key": "",
                                "value": ""
                            }],
                            cookies: [{
                                "key": "",
                                "value": ""
                            }],
                        },
                        parser: [{
                            loc: 's.parser',
                            name: 'test',
                            type: 'xpath',
                            value: 'a.test::href',
                            next: 'detail'
                        }],
                        body_location: '',
                        auto_get_body: false,
                        remove_repeats: true,
                        need_refresh: false,

                    }
                ]
            },
            tableData: [ {
                loc: 's.parser',
                name: 'test',
                type: 'xpath',
                value: 'a.test::href',
                next: 'detail'
            }],
            savedStageItems: [
                'test'
            ],
            stageName: '',
            stageUrl: '',
            stageMethod: 'GET',
            stageExternal: [""],
            stageLoop: [{
                "key": "",
                "value": ""
            }],
            stageHeaders: [{
                "key": "",
                "value": ""
            }],
            stageCookies: [{
                "key": "",
                "value": ""
            }],
            stageDeepthLimit : -1,
            stageAutoParse: false,
            stageRemoveRepeats: true,
            stageNeedRefresh: false,
            currentStage: null,
            jsonStage: '',
            jsonConfig: '',
            jsonValidation: '',
            savedEntranceItems: [],
            entranceName: '',
            currentEntranceStage: null,
            currentEntranceExternal: '',
            currentEntranceCrontab: '',
            entranceLog: ''


        },
        methods: {
            searchAllConfig: function () {
                var that = this
                $.ajax({
                    type: "get",
                    url: "/scrapyconfig/allstage",
                    dataType: 'JSON',
                    success: function (data, status) {
                        if (status == 'success') {
                            that.savedStageItems = data
                        }
                    },
                    error: function () {
                        console.log('error: bad connection with /scrapyconfig/allstage');

                    },
                    complete: function () {

                    }
                })
            },

            savedConfigSelect: function (e) {
                this.configName = e.currentTarget.innerText;
            },

            loadCurrentConfig: function () {
                var that = this
                $.ajax({
                    type: "get",
                    url: "/scrapyconfig/loadstage",
                    data: {
                        name: that.stageName
                    },
                    dataType: 'JSON',
                    success: function (data, status) {
                        if (status == 'success') {
                            // console.log(data)
                            jsonObj = JSON.parse(data[0])
                            for (var i in jsonObj.stages) {
                                jsonObj.stages[i].header.external = (jsonObj.stages[i].header.external.length == 0) ? [''] : jsonObj.stages[i].header.externa
                                jsonObj.stages[i].header.loop = that.objTransform(jsonObj.stages[i].header.loop)
                                jsonObj.stages[i].request.headers = that.objTransform(jsonObj.stages[i].request.headers)
                                jsonObj.stages[i].request.cookies = that.objTransform(jsonObj.stages[i].request.cookies)
                            }
                            that.totalConfig = jsonObj 
                            // that.stageUrl = jsonObj.request.url
                            // that.stageMethod = jsonObj.request.method
                            // that.stageExternal = (jsonObj.header.external.length == 0) ? [''] : jsonObj.header.external
                            // that.stageLoop = that.objTransform(jsonObj.header.loop)
                            // that.stageHeaders = that.objTransform(jsonObj.request.headers)
                            // that.stageCookies = that.objTransform(jsonObj.request.cookies)
                            // that.stageAutoParse = jsonObj.auto_parse
                            // that.stageRemoveRepeats = jsonObj.remove_repeats
                            // that.stageNeedRefresh = jsonObj.need_refresh
                            // that.stageDeepthLimit = jsonObj.deepth_limit
                            // that.tableData = jsonObj.parser
                            $('#table').bootstrapTable('load', jsonObj.parser)
                            // app.$mount()
                        }
                    },
                    error: function () {
                        console.log('error: bad connection with /scrapyconfig/loadstage');
                    },
                    complete: function () {}
                })
            },

            // isEmptyObject: function(obj) {

            //     for (var key in obj) {
            //         return false
            //     }
            //     return true
            // },
            objTransform: function (obj) {
                var res = []
                for (var key in obj) {
                    res.push({
                        "key": key,
                        "value": obj[key]
                    })
                }
                if (res.length == 0)
                    return [{
                        "key": "",
                        "value": ""
                    }]
                return res
            },
            addStage: function () {
                this.saveAllTable()
                this.totalConfig.stages.push(
                    {
                        name: '',
                        header: {
                            external: [''],
                            loop: [{
                                "key": "",
                                "value": ""
                            }],
                        },
                        request: {
                            url: '',
                            method: 'GET',
                            headers: [{
                                "key": "",
                                "value": ""
                            }],
                            cookies: [{
                                "key": "",
                                "value": ""
                            }],
                        },
                        parser: [{
                            loc: 's.parser',
                            name: 'test',
                            type: 'xpath',
                            value: 'a.test::href',
                            next: 'detail'
                        }],
                        body_location: '',
                        auto_get_body: false,
                        remove_repeats: true,
                        need_refresh: false,

                    }
                )
                this.refreshAllTables()
                
            },

            removeStage: function (stageIndex) {
                this.saveAllTable()
                this.totalConfig.stages.splice(stageIndex, 1)
                this.refreshAllTables()
            },


            // stageExternal
            stageExternalAdd: function (e, stageIndex) {
                this.totalConfig.stages[stageIndex].header.external.push('')
            },
            stageExternalRemove: function (e, stageIndex, index) {
                this.totalConfig.stages[stageIndex].header.external.splice(index, 1)
            },
            // stageLoop
            stageLoopAdd: function (e, stageIndex) {
                this.totalConfig.stages[stageIndex].header.loop.push({
                    "key": "",
                    "value": ""
                })
            },
            stageLoopRemove: function (e, stageIndex, index) {
                this.totalConfig.stages[stageIndex].header.loop.splice(index, 1)
            },
            // stageHeaders
            stageHeadersAdd: function (e, stageIndex) {
                this.totalConfig.stages[stageIndex].request.headers.push({
                    "key": "",
                    "value": ""
                })
            },
            stageHeadersRemove: function (e, stageIndex, index) {
                this.totalConfig.stages[stageIndex].request.headers.splice(index, 1)
            },
            // stageCookies
            stageCookiesAdd: function (e, stageIndex) {
                this.totalConfig.stages[stageIndex].request.cookies.push({
                    "key": "",
                    "value": ""
                })
            },
            stageCookiesRemove: function (e, stageIndex, index) {
                this.totalConfig.stages[stageIndex].request.cookies.splice(index, 1)
            },
            submit: function () {
                if (this.configName == '') {
                    alert('stage名称不可为空')
                    return
                }
                // var postData = {
                //     name: this.stageName,
                //     header: {
                //         external: this.arrayFilter(this.stageExternal),
                //         loop: this.arrayTransform(this.stageLoop)
                //     },
                //     request: {
                //         url: this.stageUrl,
                //         method: this.stageMethod,
                //         headers: this.arrayTransform(this.stageHeaders),
                //         cookies: this.arrayTransform(this.stageCookies)
                //     },
                //     parser: $('#table').bootstrapTable('getData'),
                //     auto_parse: this.stageAutoParse,
                //     remove_repeats: this.stageRemoveRepeats,
                //     need_refresh: this.stageNeedRefresh,
                //     deepth_limit: this.stageDeepthLimit
                // }

                // TODO: table -> config
                var postData = JSON.parse(JSON.stringify(this.totalConfig))
                for (var i in postData.stages) {
                    postData.stages[i].header.external = this.arrayFilter(postData.stages[i].header.external)
                    postData.stages[i].header.loop = this.arrayTransform(postData.stages[i].header.loop)
                    postData.stages[i].request.headers = this.arrayTransform(postData.stages[i].request.headers)
                    postData.stages[i].request.cookies = this.arrayTransform(postData.stages[i].request.cookies)

                }
                $.ajax({
                    type: "post",
                    url: "/scrapyconfig/submitstage",
                    contentType: "application/json",
                    data: JSON.stringify(postData),
                    // dataType: 'JSON',
                    success: function (data, status) {
                        if (status == 'success') {
                            alert('提交数据成功');
                        }
                    },
                    error: function () {},
                    complete: function () {

                    }
                })
            },
            arrayFilter: function (arr) {
                var res = []
                for (let i in arr) {
                    var item = arr[i]
                    if (item != null && item != '') {
                        res.pop(item)
                    }
                }
                return res
            }, 
            arrayTransform: function (arr) {
                var res = {}
                for (let i in arr) {
                    var item = arr[i]
                    res[item.key] = item.value
                }
                return res
            },
            saveAllTable: function () {
                for (var i in this.totalConfig.stages) {
                    var table = $('#table' + i)
                    if (table.length > 0) {
                        this.totalConfig.stages[i].parser = table.bootstrapTable('getData')
                    }
                }
            },  
            refreshAllTables: function () {
                console.log('refresh table.')
                this.$nextTick(() => {
                    for (var i in this.totalConfig.stages) {
                        this.loadStageTable(i)
                    }
                })
    
            },
            loadStageTable: function (stageIndex) {
                $('#table' + stageIndex.toString()).bootstrapTable({
                    theadClasses: "thead-black",
                    toolbar: '#toolbar',
                    uniqueId: 'id',
                    columns: [{
                        field: 'loc',
                        title: '嵌套位置',
                        width: 150
                    }, {
                        field: 'name',
                        title: '字段名称',
                        width: 50,
                        editable: {
                            type: 'text',
                            title: '字段名称',
                            // mode: 'inline',
                            validate: function (v) {
                                if (!v) return '字段名称不能为空';
                            }
                        }
                    }, {
                        field: 'type',
                        title: '解析类型',
                        width: 50,
                        editable: {
                            type: 'select',
                            title: '解析类型',
                            // mode: 'inline',
                            source: [{
                                value: "xpath",
                                text: "xpath"
                            },
                            {
                                value: "css",
                                text: "css"
                            },
                            {
                                value: "xpath-list",
                                text: "xpath-list"
                            },
                            {
                                value: "css-list",
                                text: "css-list"
                            },
                            {
                                value: "xpath-loop",
                                text: "xpath-loop"
                            },
                            {
                                value: "css-loop",
                                text: "css-loop"
                            },
                            {
                                value: "loop",
                                text: "loop"
                            }
                            ]
                        }
                    }, {
                        field: 'value',
                        title: '表达式',
                        width: 300,
                        editable: {
                            type: 'text',
                            title: '表达式',
                            // mode: 'inline',
                            validate: function (v) {
                                if (!v) return '表达式不能为空';
                            }
                        }
                    }, {
                        field: 'next',
                        title: '下一阶段',
                        width: 50,
                        editable: {
                            type: 'text',
                            title: '表达式',
                        }
                    }, {
                        // field: 'button',
                        title: '操作',
                        width: 200,
                        formatter: function (value, row, index) {
                            return '<div class="rowOperator{0}" index="{1}" loc="{2}" name="{3}" type="{4}" value="{5}" next="{6}"></div>'.format(stageIndex.toString(), index.toString(), row.loc, row.name, row.type, row.value, row.next)
                        }
                    }],
                    data: this.totalConfig.stages[stageIndex].parser,

                    onAll: function () {
                        $(".rowOperator{0}".format(stageIndex.toString())).each(function () { // class + id
                            var index = $(this).attr("index")
                            var loc = $(this).attr("loc")
                            var name = $(this).attr("name")
                            var type = $(this).attr("type")
                            var value = $(this).attr("value")
                            var next = $(this).attr("next")
                            console.log('.rowOperator{0}[index="{1}"]'.format(stageIndex.toString(), index.toString()))
                            new toolsComponent({
                                propsData: {
                                    tableId: '#table' + stageIndex.toString(),
                                    index: index,
                                    loc: loc,
                                    name: name,
                                    type: type,
                                    value: value,
                                    next: next
                                }
                            }).$mount('.rowOperator{0}[index="{1}"]'.format(stageIndex.toString(), index.toString()))

                        })

                    },
                    onEditableSave: function (field, row, oldValue, $el) {
                        if (field == 'name') {
                            var data = $('#table' + stageIndex.toString()).bootstrapTable('getData')
                            for (let i in data) {
                                var targetStr = row.loc + '.' + oldValue
                                var location = data[i].loc
                                if (location == targetStr || location.startsWith(targetStr + '.')) {
                                    console.log(location + ' -> ' + row.loc + '.' + row.name)
                                    data[i].loc = location.replace(targetStr, row.loc + '.' + row.name)
                                }
                            }
                            $('#table' + stageIndex.toString()).bootstrapTable('load', data)
                        }
                    }
                })
            },

            loadSelectedStage: function (e) {
                var tempName = e.currentTarget.innerText
                var that = this
                $.ajax({
                    type: "get",
                    url: "/scrapyconfig/loadstage",
                    data: {
                        name: e.currentTarget.innerText
                    },
                    dataType: 'JSON',
                    success: function (data, status) {
                        if (status == 'success') {
                            // console.log(data)
                            that.currentStage = tempName

                            that.jsonStage = JSON.stringify(JSON .parse(data[0]), null, 2)
                            that.jsonConfig = JSON.stringify(JSON.parse(data[1]), null, 2)
                            that.jsonValidation = data[2]
                        }
                    },
                    error: function () {
                        console.log('error: bad connection with /scrapyconfig/loadstage');
                    },
                    complete: function () {}
                })
            },

            validateConfig: function () {
                this.validate(this.currentStage, 0)
            },
            CorrectConfig: function () {
                this.validate(this.currentStage, 1)
            },
            validate: function (stageName, mode) {
                var that = this
                $.ajax({
                    type: "get",
                    url: "/scrapyconfig/validate",
                    data: {
                        name: stageName,
                        mode: mode
                    },
                    success: function (data, status) {
                        if (status == 'success') {
                            $.ajax({
                                type: "get",
                                url: "/scrapyconfig/loadstage",
                                data: {
                                    name: that.currentStage
                                },
                                dataType: 'JSON',
                                success: function (data, status) {
                                    if (status == 'success') {
                                        that.jsonStage = JSON.stringify(JSON.parse(data[0]), null, 2)
                                        that.jsonConfig = JSON.stringify(JSON.parse(data[1]), null, 2)
                                        that.jsonValidation = data[2]
                                    }
                                },
                                error: function () {
                                    console.log('error: bad connection with /scrapyconfig/loadstage');
                                },
                                complete: function () {}
                            })
                        }
                    },
                    error: function () {
                        console.log('error: bad connection with /scrapyconfig/validate');
                    },
                    complete: function () {}
                })
            },
            DeleteStage: function () {
                var that = this
                $.ajax({
                    type: "get",
                    url: "/scrapyconfig/deletestage",
                    data: {
                        name: that.currentStage
                    },
                    success: function (data, status) {
                        if (status == 'success') {
                            that.currentStage = null
                            that.searchAllStage()
                            that.jsonStage = ''
                            that.jsonConfig = ''
                            that.jsonValidation = ''
                        }
                    },
                    error: function () {
                        console.log('error: bad connection with /scrapyconfig/deletestage');
                    },
                    complete: function () {}
                })
            },

            searchAllEntrance: function () {
                var that = this
                $.ajax({
                    type: "get",
                    url: "/scrapyconfig/allentrance",
                    dataType: 'JSON',
                    success: function (data, status) {
                        if (status == 'success') {
                            that.savedEntranceItems = data
                        }
                    },
                    error: function () {
                        console.log('error: bad connection with /scrapyconfig/allentrance');
                    },
                    complete: function () {}
                })
            },
            savedEntranceSelect: function (e) {
                this.entranceName = e.currentTarget.innerText;
            },
            loadCurrentEntrance: function () {
                if (this.entranceName == '') {
                    alert('入口名称不可为空！')
                    return
                }
                if (this.savedEntranceItems.includes(this.entranceName)) {
                    var that = this
                    $.ajax({
                        type: "get",
                        url: "/scrapyconfig/loadentrance",
                        data: {
                            "entrance": that.entranceName
                        },
                        dataType: 'JSON',

                        success: function (data, status) {
                            if (status == 'success') {
                                that.currentEntranceStage = data.stage_name
                                that.currentEntranceExternal = data.external
                                that.currentEntranceCrontab = data.crontab
                                that.loadEntranceLog()
                            }
                        },
                        error: function () {
                            console.log('error: bad connection with /scrapyconfig/loadentrance');
                        },
                        complete: function () {}
                    })
                } else {
                    alert('找不到对应的入口')
                }
            },
            savedEntranceStageSelect: function (e) {
                this.currentEntranceStage = e.currentTarget.innerText;
            },

            entranceSubmit: function () {
                if (this.entranceName == '' || this.currentEntranceStage == null) {
                    alert('无效参数，请检查输入')
                    return
                }
                var that = this
                var postData = {
                    entrance_name: that.entranceName,
                    stage_name: that.currentEntranceStage,
                    external: that.currentEntranceExternal,
                    crontab: that.currentEntranceCrontab
                }
                $.ajax({
                    type: "post",
                    url: "/scrapyconfig/saveentrance",
                    contentType: "application/json",
                    data: JSON.stringify(postData),

                    success: function (data, status) {
                        if (status == 'success') {
                            that.searchAllEntrance()
                            alert("提交成功")
                        }
                    },
                    error: function () {
                        console.log('error: bad connection with /scrapyconfig/saveentrance');
                    },
                    complete: function () {}
                })
            },

            entranceRun: function () {
                if (this.entranceName == '' || this.currentEntranceStage == null) {
                    alert('无效参数，请检查输入')
                    return
                }
                var that = this
                var postData = {
                    entrance_name: that.entranceName,
                    stage_name: that.currentEntranceStage,
                    external: that.currentEntranceExternal,
                    crontab: that.currentEntranceCrontab
                }
                $.ajax({
                    type: "post",
                    url: "/scrapyconfig/runentrance",
                    contentType: "application/json",
                    data: JSON.stringify(postData),

                    success: function (data, status) {
                        if (status == 'success') {
                            that.searchAllEntrance()
                            alert("提交成功，已开始运行")
                        }
                    },
                    error: function () {
                        console.log('error: bad connection with /scrapyconfig/runentrance');
                    },
                    complete: function () {}
                })
            },

            entranceDelete: function () {
                if (this.entranceName == '') {
                    alert('入口名称不可为空！')
                    return
                }
                if (this.savedEntranceItems.includes(this.entranceName)) {
                    var that = this
                    $.ajax({
                        type: "get",
                        url: "/scrapyconfig/deleteentrance",
                        data: {
                            "entrance": that.entranceName
                        },
                        dataType: 'JSON',

                        success: function (data, status) {
                            if (status == 'success') {
                                that.searchAllEntrance()
                                that.entranceName = ''
                                that.currentEntranceStage = null
                                that.currentEntranceExternal = ''
                                that.currentEntranceCrontab = ''
                            }
                        },
                        error: function () {
                            console.log('error: bad connection with /scrapyconfig/loadentrance');
                        },
                        complete: function () {}
                    })
                } else {
                    alert('找不到对应的入口')
                }
            },

            loadEntranceLog: function () {
                if (this.entranceName == '') {
                    alert('入口名称不可为空！')
                    return
                }
                if (this.savedEntranceItems.includes(this.entranceName)) {
                    var that = this
                    $.ajax({
                        type: "get",
                        url: "/scrapyconfig/entrancelog",
                        data: {
                            "entrance": that.entranceName
                        },

                        success: function (data, status) {
                            if (status == 'success') {
                                log_arr = data.split('\n')
                                result = ''
                                for (var i in log_arr) {
                                    lowercaseLine = log_arr[i].toLowerCase()
                                    if (lowercaseLine.indexOf('traceback') > 0) {
                                        result += '<span class="codehl-traceback">' + log_arr[i] + '</span>'
                                    } else if (lowercaseLine.indexOf('error') > 0) {
                                        result += '<span class="codehl-error">' + log_arr[i] + '</span>'
                                    } else if (lowercaseLine.indexOf('warning') > 0) {
                                        result += '<span class="codehl-warning">' + log_arr[i] + '</span>'
                                    } else {
                                        result += '<span>' + log_arr[i] + '</span>'
                                    }
                                }
                                that.entranceLog = result
                            }
                        },
                        error: function () {
                            console.log('error: bad connection with /scrapyconfig/loadentrance');
                        },
                        complete: function () {}
                    })
                } else {
                    alert('找不到对应的入口')
                }
            }






        },
        watch: {
            pageIndex: function (val) {
                if (val == 0) {
                    this.refreshAllTables()
                } else {
                    this.searchAllStage()
                }
                if (val == 2) {
                    this.searchAllEntrance()
                }
            },

        },
        mounted: function () {
            this.refreshAllTables()
            console.log('mounted!')
            // this.$nextTick(() => {
            //     this.searchAllConfig()
            // })
            
        }
    })

});



// $.ajax({
//     type: "post",
//     url: "/scrapyconfig/table/updaterow",
//     data: row,
//     // dataType: 'JSON',
//     success: function (data, status) {
//         if (status == 'success') {
//             alert('提交数据成功');
//         }
//     },
//     error: function () {
//         alert('编辑失败');
//     },
//     complete: function () {

//     }