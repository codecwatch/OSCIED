<?php if ( ! defined('BASEPATH')) exit('No direct script access allowed');

class Metrics extends MY_Controller
{

   protected $page_name = 'metrics';

   public function __construct() {
      parent::__construct();
   }

   public function index() {
      $this->add_content('page_title', 'OSCIED - Metrics Graphs');
      $this->add_view('main', 'metrics');
      $header_data['page'] = 'metrics';
      $this->render($header_data);
   }
}
