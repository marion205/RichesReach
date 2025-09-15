/**
* Performance Monitoring Service
* Monitors app performance in production and reports metrics
*/
import { PRODUCTION_CONFIG } from '../config/production';
interface PerformanceMetric {
name: string;
value: number;
unit: string;
timestamp: Date;
screen?: string;
action?: string;
}
interface PerformanceStats {
averageLoadTime: number;
averageRenderTime: number;
memoryUsage: number;
crashRate: number;
errorRate: number;
}
class PerformanceMonitoringService {
private metrics: PerformanceMetric[] = [];
private maxMetrics = 1000;
private startTimes: Map<string, number> = new Map();
private renderTimes: Map<string, number> = new Map();
/**
* Start timing a performance metric
*/
public startTiming(name: string): void {
this.startTimes.set(name, Date.now());
}
/**
* End timing a performance metric
*/
public endTiming(name: string, screen?: string, action?: string): void {
const startTime = this.startTimes.get(name);
if (startTime) {
const duration = Date.now() - startTime;
this.recordMetric({
name,
value: duration,
unit: 'ms',
timestamp: new Date(),
screen,
action,
});
this.startTimes.delete(name);
}
}
/**
* Record a performance metric
*/
public recordMetric(metric: PerformanceMetric): void {
this.metrics.push(metric);
// Maintain metrics size limit
if (this.metrics.length > this.maxMetrics) {
this.metrics = this.metrics.slice(-this.maxMetrics);
}
// Report to analytics if enabled
if (PRODUCTION_CONFIG.ANALYTICS.ENABLED) {
this.reportMetric(metric);
}
}
/**
* Record screen load time
*/
public recordScreenLoadTime(screenName: string, loadTime: number): void {
this.recordMetric({
name: 'screen_load_time',
value: loadTime,
unit: 'ms',
timestamp: new Date(),
screen: screenName,
});
}
/**
* Record API call performance
*/
public recordApiCall(endpoint: string, duration: number, success: boolean): void {
this.recordMetric({
name: 'api_call',
value: duration,
unit: 'ms',
timestamp: new Date(),
action: `${endpoint}_${success ? 'success' : 'error'}`,
});
}
/**
* Record memory usage
*/
public recordMemoryUsage(usage: number): void {
this.recordMetric({
name: 'memory_usage',
value: usage,
unit: 'MB',
timestamp: new Date(),
});
}
/**
* Record render time for components
*/
public recordRenderTime(componentName: string, renderTime: number): void {
this.recordMetric({
name: 'component_render_time',
value: renderTime,
unit: 'ms',
timestamp: new Date(),
action: componentName,
});
}
/**
* Get performance statistics
*/
public getPerformanceStats(): PerformanceStats {
const loadTimeMetrics = this.metrics.filter(m => m.name === 'screen_load_time');
const renderTimeMetrics = this.metrics.filter(m => m.name === 'component_render_time');
const memoryMetrics = this.metrics.filter(m => m.name === 'memory_usage');
const apiMetrics = this.metrics.filter(m => m.name === 'api_call');
return {
averageLoadTime: this.calculateAverage(loadTimeMetrics),
averageRenderTime: this.calculateAverage(renderTimeMetrics),
memoryUsage: this.calculateAverage(memoryMetrics),
crashRate: 0, // Would be calculated from crash reports
errorRate: 0, // Would be calculated from error reports
};
}
/**
* Calculate average value from metrics
*/
private calculateAverage(metrics: PerformanceMetric[]): number {
if (metrics.length === 0) return 0;
const sum = metrics.reduce((acc, metric) => acc + metric.value, 0);
return sum / metrics.length;
}
/**
* Report metric to analytics service
*/
private reportMetric(metric: PerformanceMetric): void {
try {
// In a real implementation, this would send to analytics service
// Analytics.track('performance_metric', {
// name: metric.name,
// value: metric.value,
// unit: metric.unit,
// screen: metric.screen,
// action: metric.action,
// timestamp: metric.timestamp,
// });
} catch (error) {
// Don't let performance monitoring break the app
if (__DEV__) {
console.error('Performance monitoring error:', error);
}
}
}
/**
* Get metrics for a specific time range
*/
public getMetricsForTimeRange(startTime: Date, endTime: Date): PerformanceMetric[] {
return this.metrics.filter(metric => 
metric.timestamp >= startTime && metric.timestamp <= endTime
);
}
/**
* Get metrics by name
*/
public getMetricsByName(name: string): PerformanceMetric[] {
return this.metrics.filter(metric => metric.name === name);
}
/**
* Clear all metrics
*/
public clearMetrics(): void {
this.metrics = [];
this.startTimes.clear();
this.renderTimes.clear();
}
/**
* Get memory usage (if available)
*/
public getMemoryUsage(): number {
// In a real implementation, this would use a memory monitoring library
// return MemoryInfo.getUsedMemory();
return 0;
}
/**
* Monitor app performance continuously
*/
public startPerformanceMonitoring(): void {
// Monitor memory usage every 30 seconds
setInterval(() => {
const memoryUsage = this.getMemoryUsage();
if (memoryUsage > 0) {
this.recordMemoryUsage(memoryUsage);
}
}, 30000);
// Monitor app performance every minute
setInterval(() => {
const stats = this.getPerformanceStats();
this.reportPerformanceStats(stats);
}, 60000);
}
/**
* Report performance statistics
*/
private reportPerformanceStats(stats: PerformanceStats): void {
try {
// In a real implementation, this would send to analytics service
// Analytics.track('performance_stats', stats);
} catch (error) {
if (__DEV__) {
console.error('Performance stats reporting error:', error);
}
}
}
}
// Export singleton instance
export const performanceMonitoringService = new PerformanceMonitoringService();
export default performanceMonitoringService;
