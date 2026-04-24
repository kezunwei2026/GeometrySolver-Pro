import { createApp } from 'vue'
import {
  ElAlert,
  ElAside,
  ElButton,
  ElButtonGroup,
  ElCard,
  ElCol,
  ElConfigProvider,
  ElContainer,
  ElDialog,
  ElDrawer,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElMain,
  ElOption,
  ElRow,
  ElSelect,
  ElTag,
  ElTooltip,
  ElUpload,
} from 'element-plus'
import 'element-plus/es/components/alert/style/css'
import 'element-plus/es/components/aside/style/css'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/button-group/style/css'
import 'element-plus/es/components/card/style/css'
import 'element-plus/es/components/col/style/css'
import 'element-plus/es/components/config-provider/style/css'
import 'element-plus/es/components/container/style/css'
import 'element-plus/es/components/dialog/style/css'
import 'element-plus/es/components/drawer/style/css'
import 'element-plus/es/components/empty/style/css'
import 'element-plus/es/components/form/style/css'
import 'element-plus/es/components/form-item/style/css'
import 'element-plus/es/components/header/style/css'
import 'element-plus/es/components/icon/style/css'
import 'element-plus/es/components/input/style/css'
import 'element-plus/es/components/main/style/css'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/option/style/css'
import 'element-plus/es/components/row/style/css'
import 'element-plus/es/components/select/style/css'
import 'element-plus/es/components/tag/style/css'
import 'element-plus/es/components/tooltip/style/css'
import 'element-plus/es/components/upload/style/css'
import { UploadFilled } from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

app.use(router)

app.component('ElAlert', ElAlert)
app.component('ElAside', ElAside)
app.component('ElButton', ElButton)
app.component('ElButtonGroup', ElButtonGroup)
app.component('ElCard', ElCard)
app.component('ElCol', ElCol)
app.component('ElConfigProvider', ElConfigProvider)
app.component('ElContainer', ElContainer)
app.component('ElDialog', ElDialog)
app.component('ElDrawer', ElDrawer)
app.component('ElEmpty', ElEmpty)
app.component('ElForm', ElForm)
app.component('ElFormItem', ElFormItem)
app.component('ElHeader', ElHeader)
app.component('ElIcon', ElIcon)
app.component('ElInput', ElInput)
app.component('ElMain', ElMain)
app.component('ElOption', ElOption)
app.component('ElRow', ElRow)
app.component('ElSelect', ElSelect)
app.component('ElTag', ElTag)
app.component('ElTooltip', ElTooltip)
app.component('ElUpload', ElUpload)
app.component('UploadFilled', UploadFilled)

app.mount('#app')
