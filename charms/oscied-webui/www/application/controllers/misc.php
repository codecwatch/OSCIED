<?php if ( ! defined('BASEPATH')) exit('No direct script access allowed');

class Misc extends MY_Controller
{
   public function index() {
      $this->add_content('page_title', 'OSCIED - Home');
      $this->add_view('main', 'homepage');

      $header_data['page'] = 'home';
      $this->render($header_data);
   }
   
   public function contact() {
      $this->add_content('page_title', 'OSCIED - Contact Us');
      $this->add_view('main', 'contact');

      $header_data['page'] = 'contact';
      $this->render($header_data);
   }

   public function json() {
       $this->load->helper('number');
       $this->load->spark('restclient/2.1.0');
       $this->load->library('rest');
       $this->rest->initialize(
               array(
                   'server' => $this->config->item('orchestra_api_url'), 'http_auth' => 'basic',
                   'http_user' => $this->user->mail(), 'http_pass' => $this->user->secret()
                   )
               );
       $response = $this->rest->get('media');
       if ($response->status != 200) {
           print_r($response->value);
           exit;
       }
       $medias = $response->value;

       $out_array = array();
       foreach ($medias as $media) {
           if (!isset($media->metadata->measures)) continue;
           $out_array[] = array(
                "git_url" => $media->metadata->measures->git_url,
                "file" => $media->filename,
                "date" => $media->metadata->add_date,
                "metric" => "PSNR",
                "bitrate" => $media->metadata->measures->bitrate,
                "value" => $media->metadata->measures->psnr,
                "git_commit" => $media->metadata->measures->git_commit,
           );
       }
       $this->output
           ->set_content_type('application/json')
           ->set_output(json_encode($out_array));
   }
}

/* End of file misc.php */
/* Location: ./application/controllers/misc.php */
