<template>
  <div class="map-container">
    <!-- 搜索框 -->
    <div class="search-bar" v-if="showSearch">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索地点（如：宝山区、南京路、外滩）"
        size="large"
        clearable
        @input="handleSearchInput"
        @clear="handleClear"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <!-- 搜索建议列表 -->
      <div class="suggestion-list" v-if="suggestions.length > 0">
        <div
          v-for="(item, index) in suggestions"
          :key="index"
          class="suggestion-item"
          @click="handleSelectSuggestion(item)"
        >
          <div class="suggestion-name">{{ item.name }}</div>
          <div class="suggestion-address">{{ item.address || item.district }}</div>
        </div>
      </div>
    </div>

    <!-- 地图容器 -->
    <div ref="mapRef" class="map-element" :style="{ height: mapHeight }"></div>

    <!-- 已选地点信息 -->
    <div class="selected-info" v-if="selectedPlace && showSearch">
      <el-tag type="success" closable @close="handleClear">
        {{ selectedPlace.name }}
        <span v-if="selectedPlace.address"> · {{ selectedPlace.address }}</span>
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Search } from '@element-plus/icons-vue'

interface PlaceInfo {
  name: string
  address?: string
  district?: string
  location?: { lng: number; lat: number }
}

interface PoiMarker {
  name: string
  lng: number
  lat: number
  category?: string
  address?: string
}

interface RouteSegment {
  from: number
  to: number
  points: { lng: number; lat: number }[]
  distance: number
  duration: number
  from_name?: string
  to_name?: string
}

const props = withDefaults(defineProps<{
  showSearch?: boolean
  mapHeight?: string
  center?: [number, number]
  zoom?: number
  pois?: PoiMarker[]
  searchRadius?: number
  routeSegments?: RouteSegment[]
}>(), {
  showSearch: true,
  mapHeight: '400px',
  zoom: 13,
  pois: () => [],
  searchRadius: 3000,
  routeSegments: () => [],
})

const emit = defineEmits<{
  placeSelected: [place: PlaceInfo]
  placeCleared: []
}>()

const mapRef = ref<HTMLElement>()
const searchKeyword = ref('')
const suggestions = ref<PlaceInfo[]>([])
const selectedPlace = ref<PlaceInfo | null>(null)

let map: any = null
let autoComplete: any = null
let markers: any[] = []
let polylines: any[] = []
let circleMarker: any = null
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 初始化地图
onMounted(() => {
  nextTick(() => {
    if (!mapRef.value) return

    const center = props.center || [121.4737, 31.2304] // 默认上海
    map = new AMap.Map(mapRef.value, {
      zoom: props.zoom,
      center,
      resizeEnable: true,
    })

    // 初始化自动补全
    autoComplete = new AMap.AutoComplete({
      city: '全国',
    })

    // 监听地图点击
    map.on('click', (e: any) => {
      if (e.lnglat) {
        const lng = e.lnglat.getLng()
        const lat = e.lnglat.getLat()
        reverseGeocode(lng, lat)
      }
    })
  })
})

onUnmounted(() => {
  if (map) {
    map.destroy()
    map = null
  }
  if (searchTimer) clearTimeout(searchTimer)
})

// 监听 POI 变化，更新标记
watch(
  () => props.pois,
  (newPois) => {
    if (!map) return
    clearMarkers()
    if (newPois.length === 0) return

    newPois.forEach((poi, index) => {
      // 添加序号标记
      const marker = new AMap.Marker({
        position: [poi.lng, poi.lat],
        title: poi.name,
        label: {
          content: `${index + 1}. ${poi.name}`,
          direction: 'top',
        },
      })
      marker.setMap(map)
      markers.push(marker)

      // 点击弹窗
      const infoWindow = new AMap.InfoWindow({
        content: `
          <div style="padding: 8px;">
            <strong>${index + 1}. ${poi.name}</strong>
            ${poi.category ? `<br><span style="color:#909399">${poi.category}</span>` : ''}
            ${poi.address ? `<br><span style="color:#909399">${poi.address}</span>` : ''}
          </div>
        `,
        offset: new AMap.Pixel(0, -30),
      })
      marker.on('click', () => {
        infoWindow.open(map, [poi.lng, poi.lat])
      })
    })

    map.setFitView(markers)
  },
  { deep: true },
)

// 监听路线数据变化，绘制路线
watch(
  () => props.routeSegments,
  (newSegments) => {
    if (!map) return
    clearPolylines()
    if (!newSegments || newSegments.length === 0) return

    newSegments.forEach((seg) => {
      if (seg.points.length < 2) return

      const path = seg.points.map((p) => [p.lng, p.lat])

      const polyline = new AMap.Polyline({
        path,
        strokeColor: '#409eff',
        strokeWeight: 5,
        strokeOpacity: 0.8,
        lineJoin: 'round',
        lineCap: 'round',
      })
      polyline.setMap(map)
      polylines.push(polyline)
    })

    // 自适应视野
    if (markers.length > 0) {
      map.setFitView([...markers, ...polylines])
    }
  },
  { deep: true },
)

// 搜索输入
const handleSearchInput = (val: string) => {
  if (searchTimer) clearTimeout(searchTimer)
  if (!val.trim()) {
    suggestions.value = []
    return
  }
  searchTimer = setTimeout(() => {
    autoComplete.search(val, (status: string, result: any) => {
      if (status === 'complete' && result.tips) {
        suggestions.value = result.tips
          .filter((t: any) => t.location)
          .map((t: any) => ({
            name: t.name,
            address: t.address,
            district: t.district,
            location: t.location ? { lng: t.location.lng, lat: t.location.lat } : undefined,
          }))
      } else {
        suggestions.value = []
      }
    })
  }, 300)
}

// 选中搜索建议
const handleSelectSuggestion = (item: PlaceInfo) => {
  if (!item.location || !map) return

  selectedPlace.value = item
  suggestions.value = []
  searchKeyword.value = item.name

  const lng = item.location.lng
  const lat = item.location.lat

  // 定位地图
  map.setCenter([lng, lat])
  map.setZoom(14)

  // 清除旧的选中标记和圆圈
  clearCircle()

  // 添加选中标记
  const marker = new AMap.Marker({
    position: [lng, lat],
    label: { content: item.name, direction: 'top' },
  })
  marker.setMap(map)
  markers.push(marker)

  // 添加范围圆圈
  circleMarker = new AMap.CircleMarker({
    center: [lng, lat],
    radius: props.searchRadius,
    fillColor: '#409eff',
    fillOpacity: 0.1,
    strokeColor: '#409eff',
    strokeWeight: 2,
    strokeOpacity: 0.5,
  })
  circleMarker.setMap(map)

  emit('placeSelected', {
    name: item.name,
    address: item.address || item.district,
    location: { lng, lat },
  })
}

// 反向地理编码（点击地图）
const reverseGeocode = (lng: number, lat: number) => {
  const geocoder = new AMap.Geocoder()
  geocoder.getAddress([lng, lat], (status: string, result: any) => {
    if (status === 'complete' && result.regeocode) {
      const addr = result.regeocode
      const place: PlaceInfo = {
        name: addr.formattedAddress || '未知地点',
        address: addr.formattedAddress,
        location: { lng, lat },
      }
      selectedPlace.value = place
      searchKeyword.value = place.name

      clearCircle()
      circleMarker = new AMap.CircleMarker({
        center: [lng, lat],
        radius: props.searchRadius,
        fillColor: '#409eff',
        fillOpacity: 0.1,
        strokeColor: '#409eff',
        strokeWeight: 2,
        strokeOpacity: 0.5,
      })
      circleMarker.setMap(map)

      emit('placeSelected', place)
    }
  })
}

// 清除选中
const handleClear = () => {
  searchKeyword.value = ''
  suggestions.value = []
  selectedPlace.value = null
  clearCircle()
  clearMarkers()
  emit('placeCleared')
}

const clearMarkers = () => {
  markers.forEach((m) => m.setMap(null))
  markers = []
}

const clearPolylines = () => {
  polylines.forEach((p) => p.setMap(null))
  polylines = []
}

const clearCircle = () => {
  if (circleMarker) {
    circleMarker.setMap(null)
    circleMarker = null
  }
}
</script>

<style scoped>
.map-container {
  position: relative;
}

.search-bar {
  position: relative;
  z-index: 10;
  margin-bottom: 8px;
}

.suggestion-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  max-height: 300px;
  overflow-y: auto;
  z-index: 100;
}

.suggestion-item {
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.suggestion-item:hover {
  background: #f5f7fa;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-name {
  font-size: 14px;
  color: #303133;
}

.suggestion-address {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.map-element {
  width: 100%;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.selected-info {
  margin-top: 8px;
}
</style>
