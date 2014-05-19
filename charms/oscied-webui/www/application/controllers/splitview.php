<?php if ( ! defined('BASEPATH')) exit('No direct script access allowed');

class SplitView extends MY_Controller
{

   protected $page_name = 'splitview';

   public function __construct() {
      parent::__construct();
   }

   public function index() {
      $this->add_content('page_title', 'OSCIED - SplitView Graphs');
      $this->add_view('main', 'splitview');
      $header_data['page'] = 'splitview';
      $this->render($header_data);
   }
}
