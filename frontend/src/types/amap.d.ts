/** 高德地图 JS API 2.0 类型声明 */
declare namespace AMap {
  class Map {
    constructor(container: string | HTMLElement, opts?: any)
    destroy(): void
    setCenter(center: [number, number]): void
    setZoom(zoom: number): void
    setFitView(overlays?: any[]): void
    add(overlays: any | any[]): void
    remove(overlays: any | any[]): void
    clearMap(): void
    on(event: string, handler: Function): void
  }

  class Marker {
    constructor(opts?: any)
    setPosition(position: [number, number]): void
    setContent(content: string | HTMLElement): void
    setMap(map: Map | null): void
    on(event: string, handler: Function): void
    getLngLat(): { lng: number; lat: number }
  }

  class CircleMarker {
    constructor(opts?: any)
    setMap(map: Map | null): void
  }

  class InfoWindow {
    constructor(opts?: any)
    open(map: Map, position: [number, number]): void
    close(): void
    setContent(content: string | HTMLElement): void
  }

  class AutoComplete {
    constructor(opts?: any)
    search(keyword: string, callback: (status: string, result: any) => void): void
  }

  class PlaceSearch {
    constructor(opts?: any)
    searchNearBy(keyword: string, center: [number, number], radius: number, callback: (status: string, result: any) => void): void
    searchInBounds(keyword: string, bounds: any, callback: (status: string, result: any) => void): void
  }

  class Geocoder {
    constructor(opts?: any)
    getAddress(location: [number, number], callback: (status: string, result: any) => void): void
    getLocation(address: string, callback: (status: string, result: any) => void): void
  }

  class Icon {
    constructor(opts?: any)
  }

  class LngLat {
    constructor(lng: number, lat: number)
    getLng(): number
    getLat(): number
  }

  class Bounds {
    constructor(southWest: LngLat, northEast: LngLat)
  }

  class Pixel {
    constructor(x: number, y: number)
  }

  class Polyline {
    constructor(opts?: any)
    setMap(map: Map | null): void
    setPath(path: [number, number][]): void
  }
}

declare const AMap: typeof AMap
