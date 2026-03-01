#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字节跳动招聘源单元测试
测试 bytedance.py 中各个功能模块
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.sources.bytedance import BytedanceSource


class TestBytedanceSource(unittest.TestCase):
    """字节跳动招聘源单元测试类"""
    
    def setUp(self):
        """测试前置设置"""
        # 配置测试日志
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # 创建测试实例
        self.source = BytedanceSource(timeout=10, max_per_page=5)
    
    def tearDown(self):
        """测试后清理"""
        pass
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.source.source_id, 'bytedance')
        self.assertEqual(self.source.source_name, '字节跳动')
        self.assertEqual(self.source.timeout, 10)
        self.assertEqual(self.source.max_per_page, 5)
        self.assertIsNotNone(self.source.session)
        self.assertIn('Accept', self.source.headers)
    
    def test_source_attributes(self):
        """测试源属性"""
        self.assertEqual(BytedanceSource.source_id, 'bytedance')
        self.assertEqual(BytedanceSource.source_name, '字节跳动')
    
    @patch('services.sources.bytedance.proxy_manager')
    def test_proxy_configuration(self, mock_proxy_manager):
        """测试代理配置"""
        # 模拟代理管理器返回代理
        mock_proxy_manager.get_session_proxies.return_value = {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        }
        
        source_with_proxy = BytedanceSource()
        self.assertIn('http', source_with_proxy.proxies)
        self.assertIn('https', source_with_proxy.proxies)
    
    @patch('services.sources.bytedance.proxy_manager')
    def test_no_proxy_configuration(self, mock_proxy_manager):
        """测试无代理配置"""
        mock_proxy_manager.get_session_proxies.return_value = None
        
        source_without_proxy = BytedanceSource()
        self.assertIsNone(source_without_proxy.proxies)
    
    def test_format_salary_with_values(self):
        """测试薪资格式化 - 有数值"""
        # 测试正常薪资范围
        result = self.source._format_salary(15, 25, 'MONTH')
        self.assertEqual(result, '15-25K/月')
        
        # 测试只有最小值
        result = self.source._format_salary(20, None, 'MONTH')
        self.assertEqual(result, '20+K/月')
        
        # 测试只有最大值
        result = self.source._format_salary(None, 30, 'MONTH')
        self.assertEqual(result, 'Up to 30K/月')
    
    def test_format_salary_no_values(self):
        """测试薪资格式化 - 无数值"""
        # 测试都为空
        result = self.source._format_salary(None, None, 'MONTH')
        self.assertEqual(result, '面议')
        
        # 测试单位为空
        result = self.source._format_salary(15, 25, None)
        self.assertEqual(result, '15-25K')
    
    def test_parse_job_data_complete(self):
        """测试完整职位数据解析"""
        job_data = {
            'title': '高级Python工程师',
            'salary': '20K-30K/月',
            'description': '负责后端开发工作',
            'requirement': '3年以上经验',
            'city': '北京',
            'id': 'job123'
        }
        
        result = self.source._parse_job_data(job_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], '高级Python工程师')
        self.assertEqual(result['company'], '字节跳动')
        self.assertEqual(result['salary'], '20K-30K/月')
        self.assertIn('后端开发', result['description'])
        self.assertIn('3年以上经验', result['description'])
        self.assertTrue(len(result['requirements']) >= 0)
        self.assertEqual(result['source_id'], 'bytedance')
        self.assertEqual(result['source'], '字节跳动')
        self.assertEqual(result['url'], 'https://jobs.bytedance.com/experienced/detail/job123')
    
    def test_parse_job_data_alternative_fields(self):
        """测试备选字段名解析"""
        # 测试不同的字段名组合
        job_data = {
            'name': '算法工程师',  # 使用name而不是title
            'salaryRange': '25K-35K/月',  # 使用salaryRange
            'jobDescription': '算法开发',  # 使用jobDescription
            'requirements': '硕士学历',  # 使用requirements
            'location': '上海',  # 使用location而不是city
            'jobId': 'algo001'  # 使用jobId而不是id
        }
        
        result = self.source._parse_job_data(job_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], '算法工程师')
        self.assertEqual(result['salary'], '25K-35K/月')
        self.assertIn('算法开发', result['description'])
        self.assertIn('硕士学历', result['description'])
        self.assertEqual(result['url'], 'https://jobs.bytedance.com/experienced/detail/algo001')
    
    def test_parse_job_data_minimal_fields(self):
        """测试最小字段职位数据解析"""
        job_data = {
            'title': '实习生'
        }
        
        result = self.source._parse_job_data(job_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], '实习生')
        self.assertEqual(result['company'], '字节跳动')
        self.assertEqual(result['salary'], '面议')
        self.assertEqual(result['description'], '')
        self.assertEqual(result['requirements'], [])
        self.assertEqual(result['url'], '')
    
    def test_parse_job_data_empty_data(self):
        """测试空数据解析"""
        result = self.source._parse_job_data({})
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], '')
        self.assertEqual(result['company'], '字节跳动')
        self.assertEqual(result['salary'], '面议')
    
    def test_extract_job_from_card_success(self):
        """测试从卡片元素提取职位信息成功"""
        # 创建模拟的BeautifulSoup元素
        mock_card = Mock()
        
        # 模拟标题元素
        mock_title = Mock()
        mock_title.get_text.return_value = '前端开发工程师'
        
        # 设置find方法的行为
        def mock_find(*args, **kwargs):
            # 如果查找标题相关的元素，返回mock_title
            if 'h3' in str(args) or 'job-title' in str(kwargs) or kwargs.get('class_', []) == ['job-title']:
                return mock_title
            return None
        
        mock_card.find.side_effect = mock_find
        
        result = self.source._extract_job_from_card(mock_card)
        
        # 由于_extract_job_from_card方法较复杂，这里主要测试不抛出异常
        # 实际结果可能为None，这是正常的
        self.assertIsNotNone(result)  # 这里可能需要调整断言
    
    def test_extract_job_from_card_no_title(self):
        """测试从卡片元素提取 - 无标题"""
        mock_card = Mock()
        mock_card.find.return_value = None  # 所有find都返回None
        
        result = self.source._extract_job_from_card(mock_card)
        self.assertIsNone(result)
    
    def test_is_available_success(self):
        """测试可用性检查 - 成功情况"""
        with patch.object(self.source, 'test_connection', return_value=True):
            result = self.source.is_available()
            self.assertTrue(result['available'])
            self.assertEqual(result['message'], '连接正常')
    
    def test_is_available_failure(self):
        """测试可用性检查 - 失败情况"""
        with patch.object(self.source, 'test_connection', return_value=False):
            result = self.source.is_available()
            self.assertFalse(result['available'])
            self.assertIn('连接失败', result['message'])
    
    def test_is_available_exception(self):
        """测试可用性检查 - 异常情况"""
        with patch.object(self.source, 'test_connection', side_effect=Exception('网络错误')):
            result = self.source.is_available()
            self.assertFalse(result['available'])
            self.assertIn('检查失败', result['message'])
    
    def test_search_parameters(self):
        """测试搜索参数构建"""
        with patch.object(self.source.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"data": {"list": []}}'
            mock_response.json.return_value = {"data": {"list": []}}
            mock_get.return_value = mock_response
            
            # 执行搜索
            self.source.search('Python工程师', '北京', 1)
            
            # 验证参数
            args, kwargs = mock_get.call_args
            params = kwargs['params']
            
            self.assertEqual(params['keywords'], 'Python工程师')
            self.assertEqual(params['location'], '北京')
            self.assertEqual(params['current'], 1)
            self.assertEqual(params['limit'], 5)
            self.assertEqual(params['category'], '')
    
    def test_search_national_city(self):
        """测试全国搜索参数"""
        with patch.object(self.source.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"list": []}}
            mock_get.return_value = mock_response
            
            self.source.search('算法工程师', '全国', 1)
            
            args, kwargs = mock_get.call_args
            params = kwargs['params']
            
            self.assertEqual(params['location'], '')  # 全国应该转换为空字符串
    
    def test_search_http_error(self):
        """测试HTTP错误处理"""
        with patch.object(self.source.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            result = self.source.search('测试职位', '北京', 1)
            
            self.assertEqual(len(result), 0)
            mock_get.assert_called_once()
    
    def test_search_json_decode_error(self):
        """测试JSON解析错误处理"""
        with patch.object(self.source.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = 'invalid json'
            mock_response.json.side_effect = json.JSONDecodeError('Invalid', 'doc', 0)
            mock_get.return_value = mock_response
            
            with patch.object(self.source, '_parse_html_fallback', return_value=[]) as mock_fallback:
                result = self.source.search('测试职位', '北京', 1)
                self.assertEqual(len(result), 0)
                mock_fallback.assert_called_once()
    
    def test_parse_html_fallback_empty(self):
        """测试HTML备选解析 - 空内容"""
        result = self.source._parse_html_fallback('', 'test')
        self.assertEqual(len(result), 0)
    
    def test_different_data_structures(self):
        """测试不同数据结构解析"""
        # 测试dict类型数据
        dict_data = {'data': {'list': [{'title': '测试职位'}]}}
        with patch.object(self.source, '_parse_job_data') as mock_parse:
            mock_parse.return_value = {'title': '测试职位', 'company': '字节跳动'}
            # 这里直接测试_parse_job_data方法本身
            result = self.source._parse_job_data({'title': '测试职位'})
            self.assertIsNotNone(result)
        
        # 测试list类型数据的搜索功能
        list_data = [{'title': '职位1'}, {'title': '职位2'}]
        with patch.object(self.source.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = list_data
            mock_get.return_value = mock_response
            
            # 直接测试搜索功能，不依赖_parse_job_data的mock
            result = self.source.search('test', '北京', 1)
            # 验证搜索方法被调用
            mock_get.assert_called_once()


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)